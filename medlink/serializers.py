# server/medical/serializers.py

from rest_framework import serializers
from .models import MedicalFile, AppointmentRequest, Appointment



class MedicalFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalFile
        fields = '__all__'
        read_only_fields = ['uploaded_by', 'uploaded_at']
        

class AppointmentRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentRequest
        fields = '__all__'
        read_only_fields = ['status', 'requested_at', 'patient']


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'
