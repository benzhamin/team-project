from rest_framework import serializers
from django.contrib.auth import authenticate
from django.core.validators import validate_email
from .models import User, PatientProfile, DoctorProfile, Specialization, DoctorSpecialization, Review


class UserSerializer(serializers.ModelSerializer):
    """Base user serializer"""
    full_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'phone_number', 'date_of_birth', 'age', 'gender',
            'profile_picture', 'is_verified', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'is_verified']


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True, max_length=30)
    last_name = serializers.CharField(required=True, max_length=30)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'confirm_password',
            'first_name', 'last_name', 'role', 'phone_number',
            'date_of_birth', 'gender'
        ]
    
    def validate(self, data):
        # Check if passwords match
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords don't match.")
        
        # Validate email
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        
        # Validate username
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        
        return data
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        return user


class LoginUserSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if not user.is_active:
                    raise serializers.ValidationError("User account is disabled.")
                data['user'] = user
            else:
                raise serializers.ValidationError("Unable to log in with provided credentials.")
        else:
            raise serializers.ValidationError("Must include 'username' and 'password'.")
        
        return data


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_new_password = serializers.CharField(required=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError("New passwords don't match.")
        return data


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email address.")
        return value


class SpecializationSerializer(serializers.ModelSerializer):
    doctor_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Specialization
        fields = ['id', 'name', 'description', 'icon', 'is_active', 'doctor_count', 'created_at']
        read_only_fields = ['created_at']
    
    def get_doctor_count(self, obj):
        return obj.doctors.count()


class DoctorSpecializationSerializer(serializers.ModelSerializer):
    specialization = SpecializationSerializer(read_only=True)
    specialization_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = DoctorSpecialization
        fields = [
            'id', 'specialization', 'specialization_id', 'experience_years',
            'certification', 'certification_date', 'is_primary'
        ]
        read_only_fields = ['id']


class PatientProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = PatientProfile
        fields = [
            'id', 'user', 'address', 'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relationship', 'blood_type', 'allergies', 'medical_conditions',
            'current_medications', 'insurance_provider', 'insurance_number', 'bio',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        # Validate emergency contact
        if data.get('emergency_contact_phone') and not data.get('emergency_contact_name'):
            raise serializers.ValidationError("Emergency contact name is required if phone is provided.")
        
        return data


class DoctorProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    specializations = DoctorSpecializationSerializer(many=True, read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    total_reviews = serializers.IntegerField(read_only=True)
    working_days_list = serializers.ListField(read_only=True)
    
    class Meta:
        model = DoctorProfile
        fields = [
            'id', 'user', 'address', 'qualifications', 'experience_years', 'bio',
            'rating', 'total_reviews', 'average_rating', 'consultation_fee',
            'is_available', 'working_hours_start', 'working_hours_end', 'working_days',
            'working_days_list', 'specializations', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'rating', 'total_reviews', 'created_at', 'updated_at']
    
    def validate(self, data):
        # Validate working hours
        if data.get('working_hours_start') and data.get('working_hours_end'):
            if data['working_hours_start'] >= data['working_hours_end']:
                raise serializers.ValidationError("Working hours start must be before working hours end.")
        
        return data


class ReviewSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.user.get_full_name', read_only=True)
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    doctor_username = serializers.CharField(source='doctor.user.username', read_only=True)
    patient_username = serializers.CharField(source='patient.user.username', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'doctor', 'doctor_name', 'doctor_username', 'patient', 'patient_name', 'patient_username',
            'rating', 'comment', 'is_anonymous', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate(self, data):
        # Check if user has already reviewed this doctor
        if self.instance is None:  # Only check on creation
            existing_review = Review.objects.filter(
                doctor=data['doctor'],
                patient=data['patient']
            ).exists()
            
            if existing_review:
                raise serializers.ValidationError("You have already reviewed this doctor.")
        
        return data


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile information"""
    user = UserSerializer(partial=True)
    
    class Meta:
        model = PatientProfile
        fields = ['user', 'address', 'bio', 'emergency_contact_name', 'emergency_contact_phone']
    
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user
        
        # Update user fields
        for attr, value in user_data.items():
            setattr(user, attr, value)
        user.save()
        
        # Update profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance


class DoctorProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating doctor profile information"""
    user = UserSerializer(partial=True)
    
    class Meta:
        model = DoctorProfile
        fields = [
            'user', 'address', 'qualifications', 'bio', 'consultation_fee',
            'working_hours_start', 'working_hours_end', 'working_days'
        ]
    
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user
        
        # Update user fields
        for attr, value in user_data.items():
            setattr(user, attr, value)
        user.save()
        
        # Update profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance


class UserSearchSerializer(serializers.Serializer):
    """Serializer for user search functionality"""
    query = serializers.CharField(max_length=100, required=False)
    role = serializers.ChoiceField(choices=User.Role, required=False)
    specialization = serializers.CharField(max_length=100, required=False)
    min_rating = serializers.FloatField(min_value=0.0, max_value=5.0, required=False)
    max_consultation_fee = serializers.DecimalField(max_digits=8, decimal_places=2, required=False)
    available_date = serializers.DateField(required=False)
