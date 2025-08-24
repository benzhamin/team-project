# server/medical/permissions.py

from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit objects.
    """
    def has_permission(self, request, view):
        # Read permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for admins
        return request.user.is_authenticated and request.user.role == 'admin'


class IsOwnerOrDoctor(permissions.BasePermission):
    """
    Custom permission to allow owners or assigned doctors to access objects.
    """
    def has_object_permission(self, request, view, obj):
        # Admin can access everything
        if request.user.role == 'admin':
            return True
        
        # Check if user is the owner (patient)
        if hasattr(obj, 'patient') and obj.patient == request.user:
            return True
        
        # Check if user is the assigned doctor
        if hasattr(obj, 'appointment_request') and obj.appointment_request.doctor == request.user:
            return True
        
        # Check if user is the doctor in appointment request
        if hasattr(obj, 'doctor') and obj.doctor == request.user:
            return True
        
        return False


class IsPatientOrDoctor(permissions.BasePermission):
    """
    Custom permission to allow patients or doctors to access objects.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['patient', 'doctor']


class IsDoctorOnly(permissions.BasePermission):
    """
    Custom permission to only allow doctors to access objects.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'doctor'


class IsPatientOnly(permissions.BasePermission):
    """
    Custom permission to only allow patients to access objects.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'patient'


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow owners or admins to access objects.
    """
    def has_object_permission(self, request, view, obj):
        # Admin can access everything
        if request.user.role == 'admin':
            return True
        
        # Check if user is the owner
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        
        # Check if user is the owner (for different field names)
        if hasattr(obj, 'patient') and obj.patient == request.user:
            return True
        
        if hasattr(obj, 'doctor') and obj.doctor == request.user:
            return True
        
        return False


class CanManageAppointment(permissions.BasePermission):
    """
    Custom permission for appointment management.
    """
    def has_object_permission(self, request, view, obj):
        # Admin can manage everything
        if request.user.role == 'admin':
            return True
        
        # Doctor can manage appointments they're assigned to
        if request.user.role == 'doctor' and obj.appointment_request.doctor == request.user:
            return True
        
        # Patient can manage their own appointments
        if request.user.role == 'patient' and obj.appointment_request.patient == request.user:
            return True
        
        return False


class CanManageMedicalFile(permissions.BasePermission):
    """
    Custom permission for medical file management.
    """
    def has_object_permission(self, request, view, obj):
        # Admin can manage everything
        if request.user.role == 'admin':
            return True
        
        # Patient can manage their own files
        if request.user.role == 'patient' and obj.patient == request.user:
            return True
        
        # Doctor can view files of their patients
        if request.user.role == 'doctor' and obj.patient in request.user.patients.all():
            return True
        
        return False
