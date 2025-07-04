from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _




class User(AbstractUser):
    Role = (
        ('admin', _('Admin')),
        ('patient', _('Patient')),
        ('doctor', _('Doctor')),
        ('receptionist', _('Receptionist')),
    )
    role = models.CharField(
        max_length=20,
        choices=Role,
        default='patient',
        verbose_name=_('Role')
    )

    def __str__(self):
        return f"{self.id} {self.username}"


class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[('male', 'Male'),('female', 'Female')])
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Profile of {self.user.username}"
    

class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[('male', 'Male'),('female', 'Female')])
    qualifications = models.TextField(blank=True, null=True)
    experience_years = models.PositiveIntegerField(default=0)
    bio = models.TextField(blank=True, null=True)
    rating = models.FloatField(default=0.0)
    cnt = models.PositiveIntegerField(default=0)
    def __str__(self):
        return f"Profile of Dr. {self.user.username}"
    

class Specialization(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
    

class DoctorSpecialization(models.Model):
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='specializations')
    experiece_years = models.PositiveIntegerField(default=0)
    specialization = models.ForeignKey(Specialization, on_delete=models.CASCADE, related_name='doctors')

    class Meta:
        unique_together = ('doctor', 'specialization')

    def __str__(self):
        return f"{self.doctor.user.username} - {self.specialization.name}"
    

class Review(models.Model):
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='reviews')
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField()
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.patient.user.username} for Dr. {self.doctor.user.username}"
    