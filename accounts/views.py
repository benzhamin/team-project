from django.shortcuts import render
from rest_framework.views import APIView
from .serializer import *
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from django.contrib.auth import authenticate
from .models import User
from rest_framework import status

class RegisterUserView(APIView):
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user=user)
            return Response({
                'user': serializer.data,
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }, status=201)
        
        return Response({'error': serializer.errors}, status=400)

    

class LoginUserView(APIView):

    def post(self, request):
        serializers = LoginUserSerilalizer(data = request.data)
        if serializers.is_valid():
            username = request.data.get('username')    
            password = request.data.get('password')  
            user   = authenticate(username=username , password=password)
            if user:
                refresh  = RefreshToken.for_user(user=user)
                return Response({'user':serializers.data, 'refresh': str(refresh), 'access':str(refresh.access_token)},
                             status=201)
            return Response({'error': 'not fount'}, status=401)


class LogoutUserView(APIView):

    def post(self, request):
        token2=request.data.get('refresh')
        token = RefreshToken(token2)
        token.blacklist()
        return Response({'message': 'log outed'}, status=status.HTTP_205_RESET_CONTENT)
