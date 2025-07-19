from rest_framework import viewsets, permissions
from .models import Chat, Message
from .serializers import ChatSerializer, MessageSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.decorators import action

class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        chat = serializer.save()
        chat.participants.add(self.request.user)

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        message = self.get_object()
        message.is_read = True
        message.save()
        return Response({'status': 'marked as read'})
