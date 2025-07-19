from rest_framework import serializers
from .models import User, PatientProfile, DoctorProfile, Specialization, DoctorSpecialization, Review


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password', 'role']
        extra_kwargs = {'password': {'write_only': True}}

    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)  
        user.save()
        return user


class LoginUserSerilalizer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class SpecializationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialization
        fields = '__all__'


class PatientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = '__all__'
        read_only_fields = ['user']  # user will be set from request, not input



class DoctorProfileSerializer(serializers.ModelSerializer):
    specializations = serializers.SerializerMethodField()

    class Meta:
        model = DoctorProfile
        fields = ['id', 'user', 'phone_number', 'gender', 'experience_years', 'bio', 'rating', 'specializations']

    def get_specializations(self, obj):
        return [spec.specialization.name for spec in obj.specializations.all()]


class ReviewSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.user.get_full_name', read_only=True)
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'doctor', 'doctor_name', 'patient', 'patient_name', 'rating', 'comment', 'created_at']
        read_only_fields = ['created_at']
