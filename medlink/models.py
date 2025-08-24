from django.db import models
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from accounts.models import User


def validate_future_date(value):
    """Validate that the date is in the future"""
    if value <= timezone.now():
        raise ValidationError('Appointment time must be in the future.')


class MedicalFile(models.Model):
    ALLOWED_EXTENSIONS = ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'txt']
    
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medical_files')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_files')
    file = models.FileField(
        upload_to='medical_files/',
        validators=[FileExtensionValidator(allowed_extensions=ALLOWED_EXTENSIONS)]
    )
    file_type = models.CharField(max_length=10, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    is_private = models.BooleanField(default=True)

    class Meta:
        ordering = ['-uploaded_at']

    def save(self, *args, **kwargs):
        if not self.file_type:
            self.file_type = self.file.name.split('.')[-1].lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient.username} - {self.file.name}"


class AppointmentRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
    ]

    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointment_requests')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    requested_at = models.DateTimeField(auto_now_add=True)
    preferred_date = models.DateField()
    preferred_time_slot = models.CharField(
        max_length=20,
        choices=[
            ('morning', 'Morning (9 AM - 12 PM)'),
            ('afternoon', 'Afternoon (12 PM - 5 PM)'),
            ('evening', 'Evening (5 PM - 8 PM)'),
        ]
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField()
    urgency_level = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('emergency', 'Emergency'),
        ],
        default='medium'
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-requested_at']
        unique_together = ['patient', 'doctor', 'preferred_date', 'preferred_time_slot']

    def clean(self):
        if self.preferred_date < timezone.now().date():
            raise ValidationError('Preferred date cannot be in the past.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Request from {self.patient.username} to Dr. {self.doctor.username} - {self.status}"


class Appointment(models.Model):
    appointment_request = models.OneToOneField(AppointmentRequest, on_delete=models.CASCADE)
    scheduled_time = models.DateTimeField(validators=[validate_future_date])
    duration = models.PositiveIntegerField(default=30, help_text='Duration in minutes')
    accepted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='appointments_approved')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)
    is_confirmed = models.BooleanField(default=False)

    class Meta:
        ordering = ['scheduled_time']

    def clean(self):
        if self.scheduled_time <= timezone.now():
            raise ValidationError('Appointment time must be in the future.')
        
        # Check for scheduling conflicts
        conflicting_appointments = Appointment.objects.filter(
            appointment_request__doctor=self.appointment_request.doctor,
            scheduled_time__date=self.scheduled_time.date()
        ).exclude(id=self.id)
        
        for appointment in conflicting_appointments:
            if (self.scheduled_time < appointment.scheduled_time + timezone.timedelta(minutes=appointment.duration) and
                self.scheduled_time + timezone.timedelta(minutes=self.duration) > appointment.scheduled_time):
                raise ValidationError('This time slot conflicts with another appointment.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Appointment on {self.scheduled_time.strftime('%Y-%m-%d %H:%M')} with Dr. {self.appointment_request.doctor.username}"


class AppointmentReminder(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='reminders')
    reminder_time = models.DateTimeField()
    is_sent = models.BooleanField(default=False)
    reminder_type = models.CharField(
        max_length=20,
        choices=[
            ('email', 'Email'),
            ('sms', 'SMS'),
            ('push', 'Push Notification'),
        ]
    )

    class Meta:
        ordering = ['reminder_time']

    def __str__(self):
        return f"Reminder for {self.appointment} at {self.reminder_time}"
