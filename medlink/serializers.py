# server/medical/serializers.py

from rest_framework import serializers
from .models import MedicalFile, AppointmentRequest, Appointment, AppointmentReminder
from accounts.serializer import UserSerializer, DoctorProfileSerializer


class MedicalFileSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.username', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True)
    file_size = serializers.SerializerMethodField()
    
    class Meta:
        model = MedicalFile
        fields = [
            'id', 'patient', 'patient_name', 'uploaded_by', 'uploaded_by_name',
            'file', 'file_type', 'uploaded_at', 'description', 'is_private', 'file_size'
        ]
        read_only_fields = ['uploaded_by', 'uploaded_at', 'file_type', 'file_size']
    
    def get_file_size(self, obj):
        if obj.file:
            return obj.file.size
        return None
    
    def validate_file(self, value):
        # Check file size (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size cannot exceed 10MB.")
        return value


class AppointmentRequestSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.username', read_only=True)
    doctor_name = serializers.CharField(source='doctor.username', read_only=True)
    doctor_profile = DoctorProfileSerializer(source='doctor.doctor_profile', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    urgency_display = serializers.CharField(source='get_urgency_level_display', read_only=True)
    
    class Meta:
        model = AppointmentRequest
        fields = [
            'id', 'patient', 'patient_name', 'doctor', 'doctor_name', 'doctor_profile',
            'requested_at', 'preferred_date', 'preferred_time_slot', 'status', 'status_display',
            'reason', 'urgency_level', 'urgency_display', 'notes'
        ]
        read_only_fields = ['status', 'requested_at', 'patient']
    
    def validate_preferred_date(self, value):
        from django.utils import timezone
        if value < timezone.now().date():
            raise serializers.ValidationError("Preferred date cannot be in the past.")
        return value
    
    def validate(self, data):
        # Check if there's already a pending request for the same doctor, date, and time slot
        if self.instance is None:  # Only check on creation
            existing_request = AppointmentRequest.objects.filter(
                patient=data['patient'],
                doctor=data['doctor'],
                preferred_date=data['preferred_date'],
                preferred_time_slot=data['preferred_time_slot'],
                status='pending'
            ).exists()
            
            if existing_request:
                raise serializers.ValidationError(
                    "You already have a pending appointment request with this doctor for the same date and time slot."
                )
        
        return data


class AppointmentSerializer(serializers.ModelSerializer):
    appointment_request = AppointmentRequestSerializer(read_only=True)
    patient_name = serializers.CharField(source='appointment_request.patient.username', read_only=True)
    doctor_name = serializers.CharField(source='appointment_request.doctor.username', read_only=True)
    accepted_by_name = serializers.CharField(source='accepted_by.username', read_only=True)
    scheduled_time_formatted = serializers.SerializerMethodField()
    duration_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'appointment_request', 'patient_name', 'doctor_name',
            'scheduled_time', 'scheduled_time_formatted', 'duration', 'duration_formatted',
            'accepted_by', 'accepted_by_name', 'created_at', 'updated_at',
            'notes', 'is_confirmed'
        ]
        read_only_fields = ['created_at', 'updated_at', 'accepted_by']
    
    def get_scheduled_time_formatted(self, obj):
        return obj.scheduled_time.strftime('%Y-%m-%d %H:%M')
    
    def get_duration_formatted(self, obj):
        return f"{obj.duration} minutes"
    
    def validate_scheduled_time(self, value):
        from django.utils import timezone
        if value <= timezone.now():
            raise serializers.ValidationError("Appointment time must be in the future.")
        return value


class AppointmentReminderSerializer(serializers.ModelSerializer):
    appointment = AppointmentSerializer(read_only=True)
    reminder_time_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = AppointmentReminder
        fields = [
            'id', 'appointment', 'reminder_time', 'reminder_time_formatted',
            'is_sent', 'reminder_type'
        ]
        read_only_fields = ['is_sent']
    
    def get_reminder_time_formatted(self, obj):
        return obj.reminder_time.strftime('%Y-%m-%d %H:%M')


class AppointmentScheduleSerializer(serializers.Serializer):
    """Serializer for scheduling appointments"""
    doctor_id = serializers.IntegerField()
    preferred_date = serializers.DateField()
    preferred_time_slot = serializers.ChoiceField(
        choices=[
            ('morning', 'Morning (9 AM - 12 PM)'),
            ('afternoon', 'Afternoon (12 PM - 5 PM)'),
            ('evening', 'Evening (5 PM - 8 PM)'),
        ]
    )
    reason = serializers.CharField(max_length=500)
    urgency_level = serializers.ChoiceField(
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('emergency', 'Emergency'),
        ],
        default='medium'
    )
    notes = serializers.CharField(required=False, allow_blank=True)


class AppointmentRescheduleSerializer(serializers.Serializer):
    """Serializer for rescheduling appointments"""
    new_scheduled_time = serializers.DateTimeField()
    reason = serializers.CharField(max_length=200, required=False, allow_blank=True)


class MedicalFileUploadSerializer(serializers.Serializer):
    """Serializer for file uploads"""
    file = serializers.FileField()
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)
    is_private = serializers.BooleanField(default=True)
