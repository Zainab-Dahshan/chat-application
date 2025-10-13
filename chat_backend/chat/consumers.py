import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        
        # Get user from scope
        self.user = self.scope.get("user", AnonymousUser())
        
        # If user is anonymous, try to authenticate via JWT token
        if self.user.is_anonymous:
            headers = dict(self.scope.get('headers', []))
            auth_header = headers.get(b'authorization', b'').decode('utf-8')
            
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                try:
                    access_token = AccessToken(token)
                    user_id = access_token['user_id']
                    self.user = await self.get_user(user_id)
                except Exception as e:
                    print(f"Token validation error: {e}")
                    await self.close()
                    return
        
        # Only allow authenticated users to connect
        if self.user.is_anonymous:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection',
            'message': f'{self.user.username} connected to {self.room_name}',
            'username': self.user.username
        }))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json.get('message', '')
            
            if not message:
                return

            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': self.user.username,
                    'timestamp': self.get_current_timestamp()
                }
            )
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))

    async def chat_message(self, event):
        message = event['message']
        username = event.get('username', 'Unknown')
        timestamp = event.get('timestamp', '')

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': message,
            'username': username,
            'timestamp': timestamp
        }))

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return AnonymousUser()

    def get_current_timestamp(self):
        from datetime import datetime
        return datetime.now().isoformat()