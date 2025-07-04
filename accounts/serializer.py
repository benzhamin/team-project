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
    specializations = SpecializationSerializer(many=True, read_only=True)
    class Meta:
        model = DoctorProfile
        fields = '__all__, specializations'
        read_only_fields = ['user']  # user will be set from request, not input


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ['doctor', 'patient']  # doctor and patient will be set from request, not input

