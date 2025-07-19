# server/medical/serializers.py

from rest_framework import serializers
from .models import MedicalFile

class MedicalFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalFile
        fields = '__all__'
        read_only_fields = ['uploaded_by', 'uploaded_at']
        