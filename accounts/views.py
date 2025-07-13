from django.shortcuts import render
from rest_framework.views import APIView
from .serializer import *
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from django.contrib.auth import authenticate
from .models import PatientProfile, DoctorProfile, Specialization, DoctorSpecialization, Review, User
from rest_framework import status, generics, viewsets
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework import permissions




class RegisterUserView(APIView):
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user=user)
            return Response({
                'user': serializer.data,
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }, status=201)
        
        return Response({'error': serializer.errors}, status=400)

    

class LoginUserView(APIView):

    def post(self, request):
        serializers = LoginUserSerilalizer(data = request.data)
        if serializers.is_valid():
            username = request.data.get('username')    
            password = request.data.get('password')  
            user   = authenticate(username=username , password=password)
            if user:
                refresh  = RefreshToken.for_user(user=user)
                return Response({'user':serializers.data, 'refresh': str(refresh), 'access':str(refresh.access_token)},
                             status=201)
            return Response({'error': 'not fount'}, status=401)


class LogoutUserView(APIView):

    def post(self, request):
        token2=request.data.get('refresh')
        token = RefreshToken(token2)
        token.blacklist()
        return Response({'message': 'log outed'}, status=status.HTTP_205_RESET_CONTENT)


class PatientProfileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, user):
        # Get the patient profile for the logged-in user, or 404 if none
        return get_object_or_404(PatientProfile, user=user)

    def get(self, request):
        profile = self.get_object(request.user)
        serializer = PatientProfileSerializer(profile)
        return Response(serializer.data)

    def put(self, request):
        profile = self.get_object(request.user)
        serializer = PatientProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(user=request.user)  # Ensure user stays attached
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DoctorProfileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, user):
        # Get the doctor profile for the logged-in user, or 404 if none
        return get_object_or_404(DoctorProfile, user=user)

    def get(self, request):
        profile = self.get_object(request.user)
        serializer = DoctorProfileSerializer(profile)
        return Response(serializer.data)

    def put(self, request):
        profile = self.get_object(request.user)
        serializer = DoctorProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(user=request.user)  # Ensure user stays attached
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class SpecializationViewSet(viewsets.ModelViewSet):
    queryset = Specialization.objects.all()
    serializer_class = SpecializationSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()
    

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Автоустановка пациента на текущего пользователя
        serializer.save(patient=self.request.user.patient_profile)

    def get_queryset(self):
        # Фильтрация: пациент видит свои, врач — свои
        user = self.request.user
        if user.role == 'doctor':
            return Review.objects.filter(doctor=user.doctor_profile)
        elif user.role == 'patient':
            return Review.objects.filter(patient=user.patient_profile)
        return Review.objects.none()