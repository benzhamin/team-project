# server/medical/views.py

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import MedicalFile
from .serializers import MedicalFileSerializer
from .permissions import IsAdminOrReadOnly
from accounts.models import DoctorProfile, DoctorSpecialization
from accounts.serializer import DoctorProfileSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter





class MedicalFileListCreateView(generics.ListCreateAPIView):
    queryset = MedicalFile.objects.all()
    serializer_class = MedicalFileSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class MedicalFileDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MedicalFile.objects.all()
    serializer_class = MedicalFileSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]


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