from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone


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
    
    # Additional user fields
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    gender = models.CharField(
        max_length=10, 
        choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        blank=True
    )
    is_verified = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def clean(self):
        if self.date_of_birth and self.date_of_birth > timezone.now().date():
            raise ValidationError('Date of birth cannot be in the future.')
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    @property
    def age(self):
        if self.date_of_birth:
            today = timezone.now().date()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None


class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    address = models.TextField(blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True, null=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True, null=True)
    blood_type = models.CharField(
        max_length=5,
        choices=[
            ('A+', 'A+'), ('A-', 'A-'),
            ('B+', 'B+'), ('B-', 'B-'),
            ('AB+', 'AB+'), ('AB-', 'AB-'),
            ('O+', 'O+'), ('O-', 'O-'),
        ],
        blank=True
    )
    allergies = models.TextField(blank=True, null=True)
    medical_conditions = models.TextField(blank=True, null=True)
    current_medications = models.TextField(blank=True, null=True)
    insurance_provider = models.CharField(max_length=100, blank=True, null=True)
    insurance_number = models.CharField(max_length=50, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Patient Profile')
        verbose_name_plural = _('Patient Profiles')
        ordering = ['-created_at']

    def __str__(self):
        return f"Profile of {self.user.username}"
    
    def clean(self):
        if self.emergency_contact_phone and not self.emergency_contact_name:
            raise ValidationError('Emergency contact name is required if phone is provided.')
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    address = models.TextField(blank=True, null=True)
    qualifications = models.TextField(blank=True, null=True)
    experience_years = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(50)]
    )
    bio = models.TextField(blank=True, null=True)
    rating = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)]
    )
    total_reviews = models.PositiveIntegerField(default=0)
    consultation_fee = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=0.00,
        help_text='Consultation fee in dollars'
    )
    is_available = models.BooleanField(default=True)
    working_hours_start = models.TimeField(default='09:00')
    working_hours_end = models.TimeField(default='17:00')
    working_days = models.CharField(
        max_length=100,
        default='monday,tuesday,wednesday,thursday,friday',
        help_text='Comma-separated working days'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Doctor Profile')
        verbose_name_plural = _('Doctor Profiles')
        ordering = ['-rating', '-experience_years']

    def __str__(self):
        return f"Dr. {self.user.username}"
    
    def clean(self):
        if self.working_hours_start >= self.working_hours_end:
            raise ValidationError('Working hours start must be before working hours end.')
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def working_days_list(self):
        return [day.strip() for day in self.working_days.split(',')]
    
    def is_working_day(self, date):
        """Check if the given date is a working day"""
        from datetime import datetime
        day_name = date.strftime('%A').lower()
        return day_name in self.working_days_list
    
    def is_working_hour(self, time):
        """Check if the given time is within working hours"""
        return self.working_hours_start <= time <= self.working_hours_end


class Specialization(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, help_text='FontAwesome icon class')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Specialization')
        verbose_name_plural = _('Specializations')
        ordering = ['name']

    def __str__(self):
        return self.name


class DoctorSpecialization(models.Model):
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='specializations')
    specialization = models.ForeignKey(Specialization, on_delete=models.CASCADE, related_name='doctors')
    experience_years = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(50)]
    )
    certification = models.CharField(max_length=200, blank=True, null=True)
    certification_date = models.DateField(blank=True, null=True)
    is_primary = models.BooleanField(default=False, help_text='Primary specialization')

    class Meta:
        verbose_name = _('Doctor Specialization')
        verbose_name_plural = _('Doctor Specializations')
        unique_together = ('doctor', 'specialization')
        ordering = ['-is_primary', '-experience_years']

    def __str__(self):
        return f"{self.doctor.user.username} - {self.specialization.name}"
    
    def clean(self):
        if self.certification_date and self.certification_date > timezone.now().date():
            raise ValidationError('Certification date cannot be in the future.')
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Review(models.Model):
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='reviews')
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True, null=True)
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Review')
        verbose_name_plural = _('Reviews')
        unique_together = ('doctor', 'patient')
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.patient.user.username} for Dr. {self.doctor.user.username}"
    
    def save(self, *args, **kwargs):
        # Update doctor's rating when review is saved
        super().save(*args, **kwargs)
        self.update_doctor_rating()
    
    def update_doctor_rating(self):
        """Update the doctor's average rating"""
        reviews = Review.objects.filter(doctor=self.doctor)
        if reviews.exists():
            avg_rating = sum(review.rating for review in reviews) / reviews.count()
            self.doctor.rating = round(avg_rating, 1)
            self.doctor.total_reviews = reviews.count()
            self.doctor.save(update_fields=['rating', 'total_reviews'])


class UserSession(models.Model):
    """Track user sessions for analytics"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('User Session')
        verbose_name_plural = _('User Sessions')
        ordering = ['-login_time']

    def __str__(self):
        return f"Session for {self.user.username} at {self.login_time}"
    
    def end_session(self):
        """Mark session as ended"""
        self.is_active = False
        self.logout_time = timezone.now()
        self.save() 