from django.contrib import admin
from .models import User, PatientProfile, DoctorProfile, Specialization, DoctorSpecialization, Review

admin.site.register(User)
admin.site.register(PatientProfile)
admin.site.register(DoctorProfile)
admin.site.register(Specialization)
admin.site.register(DoctorSpecialization)
admin.site.register(Review)
