import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Message, MessageThread
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.thread_id = self.scope['url_route']['kwargs']['thread_id']
        self.room_group_name = f'chat_{self.thread_id}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")

        if action == "send":
            await self.handle_send(data)
        elif action == "mark_read":
            await self.handle_mark_read(data)

    async def handle_send(self, data):
        sender_id = data['sender']
        msg_type = data['type']
        text = data.get('text')
        file_url = data.get('file_url', '')

        thread = await sync_to_async(MessageThread.objects.get)(id=self.thread_id)
        sender = await sync_to_async(User.objects.get)(id=sender_id)

        message = await sync_to_async(Message.objects.create)(
            thread=thread,
            sender=sender,
            type=msg_type,
            text=text if msg_type == "text" else "",
            file=file_url if msg_type in ["image", "file"] else None
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'id': message.id,
                'sender': sender.username,
                'type_msg': msg_type,
                'text': text,
                'file': file_url,
                'timestamp': str(message.timestamp),
                'is_read': message.is_read
            }
        )

    async def handle_mark_read(self, data):
        message_id = data['message_id']
        message = await sync_to_async(Message.objects.get)(id=message_id)
        message.is_read = True
        await sync_to_async(message.save)()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'read_status',
                'message_id': message_id
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'action': 'receive',
            'message_id': event['id'],
            'sender': event['sender'],
            'type': event['type_msg'],
            'text': event['text'],
            'file': event['file'],
            'timestamp': event['timestamp'],
            'is_read': event['is_read']
        }))

    async def read_status(self, event):
        await self.send(text_data=json.dumps({
            'action': 'mark_read',
            'message_id': event['message_id']
        }))
