# server/medical/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'appointment-requests', views.AppointmentRequestViewSet, basename='appointment-request')
router.register(r'appointments', views.AppointmentViewSet, basename='appointment')
router.register(r'reminders', views.AppointmentReminderViewSet, basename='reminder')

urlpatterns = [
    # Medical Files
    path('medical-files/', views.MedicalFileListCreateView.as_view(), name='medical-file-list'),
    path('medical-files/<int:id>/', views.MedicalFileDetailView.as_view(), name='medical-file-detail'),
    
    # Doctors
    path('doctors/', views.DoctorListView.as_view(), name='doctor-list'),
    path('doctors/<int:id>/', views.DoctorDetailView.as_view(), name='doctor-detail'),
    
    # Include router URLs for appointment management
    path('', include(router.urls)),
    
    # Additional endpoints
    path('schedule-appointment/', views.AppointmentRequestViewSet.as_view({'post': 'create'}), name='schedule-appointment'),
    path('my-appointments/', views.AppointmentViewSet.as_view({'get': 'list'}), name='my-appointments'),
    path('my-requests/', views.AppointmentRequestViewSet.as_view({'get': 'list'}), name='my-requests'),
]
