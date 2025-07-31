# server/medical/views.py

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import MedicalFile, AppointmentRequest, Appointment
from rest_framework import viewsets
from .serializers import MedicalFileSerializer, AppointmentRequestSerializer, AppointmentSerializer
from .permissions import IsAdminOrReadOnly
from accounts.models import DoctorProfile, DoctorSpecialization
from accounts.serializer import DoctorProfileSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.decorators import action
from rest_framework import permissions




class MedicalFileListCreateView(generics.ListCreateAPIView):
    queryset = MedicalFile.objects.all()
    serializer_class = MedicalFileSerializer
    #permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class MedicalFileDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MedicalFile.objects.all()
    serializer_class = MedicalFileSerializer
    #permission_classes = [IsAuthenticated, IsAdminOrReadOnly]


class DoctorListView(generics.ListAPIView):
    queryset = DoctorProfile.objects.all()
    serializer_class = DoctorProfileSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['specializations__specialization__name']  # filter by specialization name
    search_fields = ['user__username', 'bio']

class DoctorDetailView(generics.RetrieveAPIView):
    queryset = DoctorProfile.objects.all()
    serializer_class = DoctorProfileSerializer
    lookup_field = 'id'  # или 'pk'


class AppointmentRequestViewSet(viewsets.ModelViewSet):
    queryset = AppointmentRequest.objects.all()
    serializer_class = AppointmentRequestSerializer

    def perform_create(self, serializer):
        serializer.save(patient=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def accept(self, request, pk=None):
        appointment_request = self.get_object()

        if appointment_request.status != 'pending':
            return Response({"error": "Already processed"}, status=400)

        time = request.data.get('scheduled_time')
        if not time:
            return Response({"error": "scheduled_time is required"}, status=400)

        appointment_request.status = 'accepted'
        appointment_request.save()

        appointment = Appointment.objects.create(
            appointment_request=appointment_request,
            scheduled_time=time,
            accepted_by=request.user
        )
        return Response(AppointmentSerializer(appointment).data, status=201)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def cancel(self, request, pk=None):
        appointment_request = self.get_object()
        appointment_request.status = 'cancelled'
        appointment_request.save()
        return Response({"status": "cancelled"})