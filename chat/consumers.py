import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Chat, Message, ChatParticipant, ChatNotification
from medlink.models import Appointment

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.chat_id}'
        self.user = self.scope['user']
        
        # Check if user is authenticated
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Check if user is participant in this chat
        if not await self.is_chat_participant():
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        
        # Update user's online status
        await self.update_user_status(True)
        
        await self.accept()
        
        # Send user joined notification
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user_id': self.user.id,
                'username': self.user.username,
                'timestamp': timezone.now().isoformat()
            }
        )

    async def disconnect(self, close_code):
        # Update user's offline status
        await self.update_user_status(False)
        
        # Send user left notification
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'user_id': self.user.id,
                'username': self.user.username,
                'timestamp': timezone.now().isoformat()
            }
        )
        
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'message')
            
            if message_type == 'message':
                await self.handle_message(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
            elif message_type == 'read_receipt':
                await self.handle_read_receipt(data)
            elif message_type == 'file_upload':
                await self.handle_file_upload(data)
            else:
                await self.send(text_data=json.dumps({
                    'error': 'Unknown message type'
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON format'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': str(e)
            }))

    async def handle_message(self, data):
        """Handle text messages"""
        message_text = data.get('message', '').strip()
        reply_to_id = data.get('reply_to')
        appointment_id = data.get('appointment_id')
        
        if not message_text:
            await self.send(text_data=json.dumps({
                'error': 'Message cannot be empty'
            }))
            return
        
        # Save message to database
        message = await self.save_message(
            message_text, 
            'text', 
            reply_to_id, 
            appointment_id
        )
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message_id': message.id,
                'sender_id': self.user.id,
                'sender_username': self.user.username,
                'message': message_text,
                'message_type': 'text',
                'timestamp': message.timestamp.isoformat(),
                'reply_to': reply_to_id,
                'appointment_id': appointment_id
            }
        )
        
        # Create notifications for other participants
        await self.create_notifications(message)

    async def handle_typing(self, data):
        """Handle typing indicators"""
        is_typing = data.get('is_typing', False)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_typing',
                'user_id': self.user.id,
                'username': self.user.username,
                'is_typing': is_typing
            }
        )

    async def handle_read_receipt(self, data):
        """Handle read receipts"""
        message_id = data.get('message_id')
        if message_id:
            await self.mark_message_read(message_id)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'message_read',
                    'message_id': message_id,
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'timestamp': timezone.now().isoformat()
                }
            )

    async def handle_file_upload(self, data):
        """Handle file uploads (placeholder for file handling)"""
        # This would typically handle file uploads via a separate endpoint
        # For now, we'll just acknowledge the request
        await self.send(text_data=json.dumps({
            'type': 'file_upload_ack',
            'status': 'File uploads should be handled via HTTP endpoints'
        }))

    # WebSocket event handlers
    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message_id': event['message_id'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'message': event['message'],
            'message_type': event['message_type'],
            'timestamp': event['timestamp'],
            'reply_to': event.get('reply_to'),
            'appointment_id': event.get('appointment_id')
        }))

    async def user_typing(self, event):
        """Send typing indicator to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_typing': event['is_typing']
        }))

    async def user_joined(self, event):
        """Send user joined notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp']
        }))

    async def user_left(self, event):
        """Send user left notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp']
        }))

    async def message_read(self, event):
        """Send read receipt to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'message_read',
            'message_id': event['message_id'],
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp']
        }))

    # Database operations
    @database_sync_to_async
    def is_chat_participant(self):
        """Check if user is a participant in this chat"""
        try:
            chat = Chat.objects.get(id=self.chat_id, is_active=True)
            return chat.participants.filter(id=self.user.id).exists()
        except Chat.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, text, message_type, reply_to_id=None, appointment_id=None):
        """Save message to database"""
        try:
            chat = Chat.objects.get(id=self.chat_id)
            
            message = Message.objects.create(
                chat=chat,
                sender=self.user,
                text=text,
                message_type=message_type
            )
            
            if reply_to_id:
                try:
                    reply_message = Message.objects.get(id=reply_to_id, chat=chat)
                    message.reply_to = reply_message
                    message.save()
                except Message.DoesNotExist:
                    pass
            
            if appointment_id:
                try:
                    appointment = Appointment.objects.get(id=appointment_id)
                    message.appointment = appointment
                    message.save()
                except Appointment.DoesNotExist:
                    pass
            
            return message
        except Chat.DoesNotExist:
            raise Exception("Chat not found")

    @database_sync_to_async
    def mark_message_read(self, message_id):
        """Mark message as read"""
        try:
            message = Message.objects.get(id=message_id)
            message.mark_as_read(self.user)
        except Message.DoesNotExist:
            pass

    @database_sync_to_async
    def update_user_status(self, is_online):
        """Update user's online status"""
        try:
            chat = Chat.objects.get(id=self.chat_id)
            participant, created = ChatParticipant.objects.get_or_create(
                chat=chat,
                user=self.user
            )
            participant.is_online = is_online
            participant.update_last_seen()
        except Chat.DoesNotExist:
            pass

    @database_sync_to_async
    def create_notifications(self, message):
        """Create notifications for other chat participants"""
        try:
            chat = message.chat
            other_participants = chat.participants.exclude(id=self.user.id)
            
            for participant in other_participants:
                ChatNotification.objects.create(
                    user=participant,
                    chat=chat,
                    message=message,
                    notification_type='new_message',
                    title=f'New message from {self.user.username}',
                    body=message.text[:100] + '...' if len(message.text) > 100 else message.text
                )
        except Exception:
            pass


class NotificationConsumer(AsyncWebsocketConsumer):
    """Consumer for handling user notifications"""
    
    async def connect(self):
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        self.user_group_name = f'user_{self.user.id}'
        
        await self.channel_layer.group_add(self.user_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.user_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'mark_read':
                notification_id = data.get('notification_id')
                await self.mark_notification_read(notification_id)
            elif action == 'mark_all_read':
                await self.mark_all_notifications_read()
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({'error': 'Invalid JSON format'}))

    async def notification_message(self, event):
        """Send notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification_id': event['notification_id'],
            'title': event['title'],
            'body': event['body'],
            'notification_type': event['notification_type'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark specific notification as read"""
        try:
            notification = ChatNotification.objects.get(
                id=notification_id,
                user=self.user
            )
            notification.mark_as_read()
        except ChatNotification.DoesNotExist:
            pass

    @database_sync_to_async
    def mark_all_notifications_read(self):
        """Mark all user notifications as read"""
        ChatNotification.objects.filter(
            user=self.user,
            is_read=False
        ).update(is_read=True)
