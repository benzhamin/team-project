from rest_framework import serializers
from .models import Message

class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.StringRelatedField()

    class Meta:
        model = Message
        fields = ['id', 'sender', 'type', 'text', 'file', 'timestamp', 'is_read']
        read_only_fields = ['id', 'timestamp', 'is_read']