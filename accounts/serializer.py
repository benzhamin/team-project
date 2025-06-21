from rest_framework import serializers
from .models import User 


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