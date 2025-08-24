# server/medical/views.py

from rest_framework import generics, viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta

from .models import MedicalFile, AppointmentRequest, Appointment, AppointmentReminder
from .serializers import (
    MedicalFileSerializer, 
    AppointmentRequestSerializer, 
    AppointmentSerializer,
    AppointmentReminderSerializer
)
from .permissions import IsAdminOrReadOnly, IsOwnerOrDoctor
from accounts.models import DoctorProfile, DoctorSpecialization
from accounts.serializer import DoctorProfileSerializer


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class MedicalFileFilter(filters.FilterSet):
    file_type = filters.CharFilter(lookup_expr='icontains')
    uploaded_after = filters.DateTimeFilter(field_name='uploaded_at', lookup_expr='gte')
    uploaded_before = filters.DateTimeFilter(field_name='uploaded_at', lookup_expr='lte')
    
    class Meta:
        model = MedicalFile
        fields = ['file_type', 'is_private']


class MedicalFileListCreateView(generics.ListCreateAPIView):
    serializer_class = MedicalFileSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = MedicalFileFilter
    search_fields = ['description', 'file_type']
    ordering_fields = ['uploaded_at', 'file_type']
    ordering = ['-uploaded_at']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'doctor':
            # Doctors can see files of their patients
            return MedicalFile.objects.filter(patient__in=user.patients.all())
        elif user.role == 'patient':
            # Patients can only see their own files
            return MedicalFile.objects.filter(patient=user)
        elif user.role == 'admin':
            # Admins can see all files
            return MedicalFile.objects.all()
        return MedicalFile.objects.none()

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user, patient=self.request.user)


class MedicalFileDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MedicalFileSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrDoctor]
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        if user.role == 'doctor':
            return MedicalFile.objects.filter(patient__in=user.patients.all())
        elif user.role == 'patient':
            return MedicalFile.objects.filter(patient=user)
        elif user.role == 'admin':
            return MedicalFile.objects.all()
        return MedicalFile.objects.none()


class DoctorFilter(filters.FilterSet):
    specialization = filters.CharFilter(field_name='specializations__specialization__name', lookup_expr='icontains')
    experience_min = filters.NumberFilter(field_name='experience_years', lookup_expr='gte')
    experience_max = filters.NumberFilter(field_name='experience_years', lookup_expr='lte')
    rating_min = filters.NumberFilter(field_name='rating', lookup_expr='gte')
    available_date = filters.DateFilter(method='filter_available_date')
    
    class Meta:
        model = DoctorProfile
        fields = ['specialization', 'experience_min', 'experience_max', 'rating_min', 'available_date']
    
    def filter_available_date(self, queryset, name, value):
        """Filter doctors available on a specific date"""
        if value:
            # Get doctors who don't have appointments on this date
            busy_doctors = Appointment.objects.filter(
                scheduled_time__date=value
            ).values_list('appointment_request__doctor', flat=True)
            return queryset.exclude(user__id__in=busy_doctors)
        return queryset


class DoctorListView(generics.ListAPIView):
    queryset = DoctorProfile.objects.all()
    serializer_class = DoctorProfileSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = DoctorFilter
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'bio', 'qualifications']
    ordering_fields = ['rating', 'experience_years', 'user__username']
    ordering = ['-rating', '-experience_years']

    def get_queryset(self):
        queryset = super().get_queryset()
        # Only show active doctors
        return queryset.filter(user__is_active=True)


class DoctorDetailView(generics.RetrieveAPIView):
    queryset = DoctorProfile.objects.all()
    serializer_class = DoctorProfileSerializer
    lookup_field = 'id'

    def get_queryset(self):
        return DoctorProfile.objects.filter(user__is_active=True)


class AppointmentRequestFilter(filters.FilterSet):
    status = filters.CharFilter(lookup_expr='exact')
    urgency_level = filters.CharFilter(lookup_expr='exact')
    preferred_date = filters.DateFilter(lookup_expr='exact')
    preferred_date_after = filters.DateFilter(field_name='preferred_date', lookup_expr='gte')
    preferred_date_before = filters.DateFilter(field_name='preferred_date', lookup_expr='lte')
    
    class Meta:
        model = AppointmentRequest
        fields = ['status', 'urgency_level', 'preferred_date']


class AppointmentRequestViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentRequestSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = AppointmentRequestFilter
    search_fields = ['reason', 'notes']
    ordering_fields = ['requested_at', 'preferred_date', 'urgency_level']
    ordering = ['-requested_at']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'doctor':
            return AppointmentRequest.objects.filter(doctor=user)
        elif user.role == 'patient':
            return AppointmentRequest.objects.filter(patient=user)
        elif user.role == 'admin':
            return AppointmentRequest.objects.all()
        return AppointmentRequest.objects.none()

    def perform_create(self, serializer):
        serializer.save(patient=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def accept(self, request, pk=None):
        appointment_request = self.get_object()
        
        # Check if user is the doctor for this request
        if request.user != appointment_request.doctor:
            return Response(
                {"error": "Only the assigned doctor can accept this request"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        if appointment_request.status != 'pending':
            return Response(
                {"error": "Request has already been processed"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        scheduled_time_str = request.data.get('scheduled_time')
        if not scheduled_time_str:
            return Response(
                {"error": "scheduled_time is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            scheduled_time = datetime.fromisoformat(scheduled_time_str.replace('Z', '+00:00'))
        except ValueError:
            return Response(
                {"error": "Invalid datetime format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate scheduled time is in the future
        if scheduled_time <= timezone.now():
            return Response(
                {"error": "Scheduled time must be in the future"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check for scheduling conflicts
        conflicting_appointments = Appointment.objects.filter(
            appointment_request__doctor=appointment_request.doctor,
            scheduled_time__date=scheduled_time.date()
        )
        
        duration = int(request.data.get('duration', 30))
        
        for appointment in conflicting_appointments:
            if (scheduled_time < appointment.scheduled_time + timedelta(minutes=appointment.duration) and
                scheduled_time + timedelta(minutes=duration) > appointment.scheduled_time):
                return Response(
                    {"error": "This time slot conflicts with another appointment"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

        appointment_request.status = 'accepted'
        appointment_request.save()

        appointment = Appointment.objects.create(
            appointment_request=appointment_request,
            scheduled_time=scheduled_time,
            duration=duration,
            accepted_by=request.user
        )

        # Create reminder for the appointment
        reminder_time = scheduled_time - timedelta(hours=24)
        if reminder_time > timezone.now():
            AppointmentReminder.objects.create(
                appointment=appointment,
                reminder_time=reminder_time,
                reminder_type='email'
            )

        return Response(AppointmentSerializer(appointment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reject(self, request, pk=None):
        appointment_request = self.get_object()
        
        if request.user != appointment_request.doctor:
            return Response(
                {"error": "Only the assigned doctor can reject this request"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        if appointment_request.status != 'pending':
            return Response(
                {"error": "Request has already been processed"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment_request.status = 'rejected'
        appointment_request.save()
        
        return Response({"status": "rejected"})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        appointment_request = self.get_object()
        
        if request.user not in [appointment_request.patient, appointment_request.doctor]:
            return Response(
                {"error": "Only the patient or doctor can cancel this request"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        if appointment_request.status not in ['pending', 'accepted']:
            return Response(
                {"error": "Cannot cancel a request that is already cancelled or rejected"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment_request.status = 'cancelled'
        appointment_request.save()
        
        return Response({"status": "cancelled"})


class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['scheduled_time', 'created_at']
    ordering = ['scheduled_time']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'doctor':
            return Appointment.objects.filter(appointment_request__doctor=user)
        elif user.role == 'patient':
            return Appointment.objects.filter(appointment_request__patient=user)
        elif user.role == 'admin':
            return Appointment.objects.all()
        return Appointment.objects.none()

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def confirm(self, request, pk=None):
        appointment = self.get_object()
        
        if request.user != appointment.appointment_request.patient:
            return Response(
                {"error": "Only the patient can confirm this appointment"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        appointment.is_confirmed = True
        appointment.save()
        
        return Response({"status": "confirmed"})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reschedule(self, request, pk=None):
        appointment = self.get_object()
        
        if request.user not in [appointment.appointment_request.patient, appointment.appointment_request.doctor]:
            return Response(
                {"error": "Only the patient or doctor can reschedule this appointment"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        new_time_str = request.data.get('new_scheduled_time')
        if not new_time_str:
            return Response(
                {"error": "new_scheduled_time is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            new_time = datetime.fromisoformat(new_time_str.replace('Z', '+00:00'))
        except ValueError:
            return Response(
                {"error": "Invalid datetime format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_time <= timezone.now():
            return Response(
                {"error": "New scheduled time must be in the future"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment.scheduled_time = new_time
        appointment.is_confirmed = False
        appointment.save()
        
        return Response(AppointmentSerializer(appointment).data)


class AppointmentReminderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AppointmentReminderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        if user.role == 'doctor':
            return AppointmentReminder.objects.filter(appointment__appointment_request__doctor=user)
        elif user.role == 'patient':
            return AppointmentReminder.objects.filter(appointment__appointment_request__patient=user)
        elif user.role == 'admin':
            return AppointmentReminder.objects.all()
        return AppointmentReminder.objects.none()