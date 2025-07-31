# server/medical/urls.py

from django.urls import path, include
from .views import MedicalFileListCreateView, MedicalFileDetailView, DoctorListView, DoctorDetailView, AppointmentRequestViewSet
from rest_framework.routers import DefaultRouter




medical_file = [
    path('files/', MedicalFileListCreateView.as_view(), name='medicalfile-list-create'),
    path('files/<int:pk>/', MedicalFileDetailView.as_view(), name='medicalfile-detail'),
]

# Doctor-related URLs
doc = [
    path('doctors/', DoctorListView.as_view(), name='doctor-list'),
    path('doctors/<int:id>/', DoctorDetailView.as_view(), name='doctor-detail'),
]

router = DefaultRouter()
router.register('appointment-requests', AppointmentRequestViewSet)

urlpatterns = [
    path('medical/', include(medical_file)),  # Medical file endpoints at the root
    path('', include(doc)),  # Doctor endpoints at the root
    path('', include(router.urls)),  # Weekly availability and appointment endpoints at the root
]
