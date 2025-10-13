import json
import logging
import traceback
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import ChatRoom, ChatMessage, UserRoom, Notification, UserPresence

User = get_user_model()

# Set up loggers
logger = logging.getLogger('chat.websocket')
security_logger = logging.getLogger('chat.security')

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            # Extract room name from URL
            self.room_name = self.scope['url_route']['kwargs']['room_name']
            self.room_group_name = f'chat_{self.room_name}'
            
            logger.info(f"WebSocket connection attempt for room: {self.room_name}")
            
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
                        logger.info(f"JWT authentication successful for user_id: {user_id}")
                    except Exception as e:
                        logger.error(f"JWT token validation error: {str(e)}")
                        security_logger.warning(f"Failed JWT authentication attempt: {str(e)}")
                        await self.close(code=4401, reason="Authentication failed")
                        return
                else:
                    logger.warning("No valid authentication header provided")
                    security_logger.warning("Anonymous WebSocket connection attempt without authentication")
                    await self.close(code=4401, reason="Authentication required")
                    return
            
            # Only allow authenticated users to connect
            if self.user.is_anonymous:
                logger.warning("Anonymous user attempted to connect")
                security_logger.warning("Anonymous WebSocket connection attempt")
                await self.close(code=4401, reason="Authentication required")
                return

            # Log successful authentication
            logger.info(f"User {self.user.username} authenticated successfully")
            
            # Update user presence
            await self.update_user_presence(True, self.room_name)

            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            logger.info(f"User {self.user.username} joined room group: {self.room_group_name}")

            await self.accept()
            
            # Send connection confirmation
            connection_message = {
                'type': 'connection',
                'message': f'{self.user.username} connected to {self.room_name}',
                'username': self.user.username
            }
            
            await self.send(text_data=json.dumps(connection_message))
            logger.info(f"Connection accepted for user {self.user.username} in room {self.room_name}")
            
        except KeyError as e:
            logger.error(f"Missing required parameter in WebSocket connection: {str(e)}")
            await self.close(code=4400, reason="Invalid connection parameters")
        except Exception as e:
            logger.error(f"Unexpected error during WebSocket connection: {str(e)}")
            logger.error(traceback.format_exc())
            await self.close(code=4400, reason="Internal server error")

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        try:
            logger.info(f"WebSocket disconnect for user {getattr(self, 'user', 'unknown')} from room {getattr(self, 'room_name', 'unknown')}, close_code: {close_code}")
            
            # Leave room group if it exists
            if hasattr(self, 'room_group_name') and hasattr(self, 'channel_name'):
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )
                # Update user presence
                await self.update_user_presence(False, None)
                logger.info(f"User {getattr(self, 'user', 'unknown')} left room group: {self.room_group_name}")
            else:
                logger.warning("Disconnect called but room_group_name or channel_name not set")
                
        except Exception as e:
            logger.error(f"Error during WebSocket disconnect: {str(e)}")
            logger.error(traceback.format_exc())

    async def create_notification(self, recipient_id, notification_type, title, message, related_message_id=None, room_name=None):
        """Create a notification for a user"""
        try:
            await self.save_notification(
                recipient_id=recipient_id,
                sender_id=self.user.id if self.user else None,
                notification_type=notification_type,
                title=title,
                message=message,
                related_message_id=related_message_id,
                room_name=room_name
            )
            logger.info(f"Notification created: {notification_type} for user {recipient_id}")
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")

    async def update_user_presence(self, is_online, current_room):
        """Update user presence status"""
        try:
            await self.save_user_presence(
                user_id=self.user.id,
                is_online=is_online,
                current_room=current_room
            )
            logger.info(f"User presence updated: {self.user.username} - online: {is_online}")
        except Exception as e:
            logger.error(f"Error updating user presence: {str(e)}")

    @database_sync_to_async
    def save_notification(self, recipient_id, sender_id, notification_type, title, message, related_message_id=None, room_name=None):
        """Save notification to database"""
        notification = Notification.objects.create(
            recipient_id=recipient_id,
            sender_id=sender_id,
            notification_type=notification_type,
            title=title,
            message=message,
            related_message_id=related_message_id,
            room_name=room_name
        )
        return notification

    @database_sync_to_async
    def save_user_presence(self, user_id, is_online, current_room):
        """Save user presence to database"""
        UserPresence.objects.update_or_create(
            user_id=user_id,
            defaults={
                "is_online": is_online,
                "current_room": current_room
            }
        )

    @database_sync_to_async
    def save_message(self, message, room_name):
        """Save message to database"""
        try:
            room = ChatRoom.objects.get(name=room_name)
        except ChatRoom.DoesNotExist:
            # Create the room if it doesn't exist
            room = ChatRoom.objects.create(name=room_name)
            logger.info(f"Created new room: {room_name}")
        
        chat_message = ChatMessage.objects.create(
            room=room,
            user=self.user,
            message=message
        )
        return chat_message

    async def receive(self, text_data):
        try:
            logger.info(f"Received message from user {self.user.username} in room {self.room_name}")
            
            # Validate input
            if not text_data:
                logger.warning("Empty message received")
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Empty message received'
                }))
                return
            
            # Parse JSON
            try:
                text_data_json = json.loads(text_data)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON format from user {self.user.username}: {str(e)}")
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Invalid JSON format'
                }))
                return
            
            # Extract message
            message = text_data_json.get('message', '').strip()
            
            if not message:
                logger.warning(f"Empty message content from user {self.user.username}")
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Message content cannot be empty'
                }))
                return
            
            # Validate message length
            if len(message) > 1000:
                logger.warning(f"Message too long from user {self.user.username}: {len(message)} characters")
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Message too long (max 1000 characters)'
                }))
                return
            
            # Log the message
            logger.info(f"User {self.user.username} sending message in room {self.room_name}: {message[:50]}...")
            
            # Save message to database
            chat_message = await self.save_message(message, self.room_name)
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': self.user.username,
                    'timestamp': self.get_current_timestamp(),
                    'message_id': chat_message.id
                }
            )
            
            logger.info(f"Message broadcasted successfully from user {self.user.username}")
            
        except Exception as e:
            logger.error(f"Error processing message from user {self.user.username}: {str(e)}")
            logger.error(traceback.format_exc())
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error while processing message'
            }))

    async def chat_message(self, event):
        """Handle chat messages"""
        try:
            message = event['message']
            username = event['username']
            timestamp = event['timestamp']
            message_id = event.get('message_id')
            
            logger.info(f"Broadcasting message to user {self.user.username} in room {self.room_name}: {message[:50]}...")
            
            # Validate event data
            if not all([message, username, timestamp]):
                logger.warning(f"Incomplete message event data: {event}")
                return
            
            # Send message to WebSocket
            await self.send(text_data=json.dumps({
                'type': 'chat_message',
                'message': message,
                'username': username,
                'timestamp': timestamp,
                'message_id': message_id
            }))
            
            # Create notifications for offline users in the room
            if self.user.username != username:  # Don't notify self
                await self.create_notifications_for_offline_users(message, username, message_id)
            
            logger.info(f"Message successfully sent to user {self.user.username}")
            
        except KeyError as e:
            logger.error(f"Missing required field in chat_message event: {str(e)}")
            logger.error(f"Event data: {event}")
        except Exception as e:
            logger.error(f"Error sending chat message to user {self.user.username}: {str(e)}")
            logger.error(traceback.format_exc())

    async def create_notifications_for_offline_users(self, message_content, sender_username, message_id):
        """Create notifications for offline users in the room"""
        try:
            # Get all users in the room except the sender
            room_users = await self.get_room_users()
            for user in room_users:
                if user.username != sender_username:
                    # Check if user is offline
                    is_online = await self.check_user_online(user.id)
                    if not is_online:
                        await self.create_notification(
                            recipient_id=user.id,
                            notification_type='message',
                            title=f'New message from {sender_username}',
                            message=message_content,
                            related_message_id=message_id,
                            room_name=self.room_name
                        )
        except Exception as e:
            logger.error(f'Error creating notifications for offline users: {str(e)}')

    @database_sync_to_async
    def get_room_users(self):
        """Get all users in the current room"""
        room = ChatRoom.objects.get(name=self.room_name)
        user_ids = UserRoom.objects.filter(room=room).values_list('user_id', flat=True)
        return User.objects.filter(id__in=user_ids)

    @database_sync_to_async
    def check_user_online(self, user_id):
        """Check if user is online"""
        try:
            presence = UserPresence.objects.get(user_id=user_id)
            return presence.is_online
        except UserPresence.DoesNotExist:
            return False

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            logger.info("Attempting to validate JWT token")
            
            # Validate user_id format
            if not user_id:
                logger.warning("No user_id provided")
                return AnonymousUser()
            
            user = User.objects.get(id=user_id)
            logger.info(f"Successfully authenticated user: {user.username} (ID: {user.id})")
            return user
            
        except User.DoesNotExist:
            logger.warning(f"User with ID {user_id} does not exist")
            return AnonymousUser()
        except Exception as e:
            logger.warning(f"Token validation failed: {str(e)}")
            return AnonymousUser()

    def get_current_timestamp(self):
        try:
            from datetime import datetime, timezone
            
            # Use timezone-aware datetime with built-in timezone support
            timestamp = datetime.now(timezone.utc).isoformat()
            logger.debug(f"Generated timestamp: {timestamp}")
            return timestamp
            
        except Exception as e:
            logger.error(f"Error generating timestamp: {str(e)}")
            # Fallback to simple datetime
            from datetime import datetime
            return datetime.now().isoformat()