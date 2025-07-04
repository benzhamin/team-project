# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, PatientProfile, DoctorProfile, Review

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created and instance.role == 'patient':
        PatientProfile.objects.create(user=instance)
    if created and instance.role == 'doctor':
        DoctorProfile.objects.create(user=instance)


@receiver(post_save, sender=Review)
def doctor_rating(sender, instance, created, **kwargs):
    if created:
        doctor = instance.doctor
        doctor.rating = (doctor.rating * doctor.cnt + instance.rating) / (doctor.cnt + 1)
        doctor.cnt += 1
        doctor.save()