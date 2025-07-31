from django.db import models
from accounts.models import User


# 📁 Медицинские файлы
class MedicalFile(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medical_files')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_files')
    file = models.FileField(upload_to='medical_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.patient} - {self.file.name}"
    

# models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class AppointmentRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('cancelled', 'Cancelled'),
    ]

    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointment_requests')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    requested_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField(blank=True)

    def __str__(self):
        return f"Request from {self.patient.username} to {self.doctor.username} - {self.status}"


class Appointment(models.Model):
    appointment_request = models.OneToOneField(AppointmentRequest, on_delete=models.CASCADE)
    scheduled_time = models.DateTimeField()
    accepted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='appointments_approved')

    def __str__(self):
        return f"Appointment on {self.scheduled_time} with Dr. {self.appointment_request.doctor.username}"
