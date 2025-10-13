from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, UserSerializer, ChatRoomSerializer, ChatMessageSerializer, UserRoomSerializer, NotificationSerializer, UserPresenceSerializer
from .models import ChatRoom, ChatMessage, UserRoom, Notification, UserPresence


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens for the new user
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'user': serializer.data,
            'message': 'Profile updated successfully'
        })


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ChatRoomListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ChatRoom.objects.all()

    def perform_create(self, serializer):
        room = serializer.save()
        # Automatically add the creator to the room
        UserRoom.objects.create(user=self.request.user, room=room)


class ChatRoomMessagesView(generics.ListAPIView):
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        room_id = self.kwargs['room_id']
        return ChatMessage.objects.filter(room_id=room_id).order_by('timestamp')


class SendMessageView(generics.CreateAPIView):
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        room_id = self.kwargs['room_id']
        serializer.save(user=self.request.user, room_id=room_id)


class JoinRoomView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, room_id):
        try:
            room = ChatRoom.objects.get(id=room_id)
            user_room, created = UserRoom.objects.get_or_create(
                user=request.user, room=room
            )
            if created:
                return Response({'message': 'Successfully joined room'}, status=status.HTTP_201_CREATED)
            else:
                return Response({'message': 'Already in room'}, status=status.HTTP_200_OK)
        except ChatRoom.DoesNotExist:
            return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)


class LeaveRoomView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, room_id):
        try:
            user_room = UserRoom.objects.get(user=request.user, room_id=room_id)
            user_room.delete()
            return Response({'message': 'Successfully left room'}, status=status.HTTP_200_OK)
        except UserRoom.DoesNotExist:
            return Response({'error': 'Not a member of this room'}, status=status.HTTP_404_NOT_FOUND)


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    """Get user's notifications"""
    try:
        notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
        
        # Filter by read status if provided
        is_read = request.query_params.get('is_read')
        if is_read is not None:
            is_read = is_read.lower() == 'true'
            notifications = notifications.filter(is_read=is_read)
        
        # Filter by notification type if provided
        notification_type = request.query_params.get('type')
        if notification_type:
            notifications = notifications.filter(notification_type=notification_type)
        
        serializer = NotificationSerializer(notifications, many=True)
        logger.info(f'User {request.user.username} retrieved {len(notifications)} notifications')
        return Response(serializer.data)
    except Exception as e:
        logger.error(f'Error getting notifications: {str(e)}')
        return Response(
            {'error': 'Failed to get notifications'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    try:
        notification = Notification.objects.get(id=notification_id, recipient=request.user)
        notification.is_read = True
        notification.save()
        
        logger.info(f'User {request.user.username} marked notification {notification_id} as read')
        return Response({'message': 'Notification marked as read'})
    except Notification.DoesNotExist:
        return Response(
            {'error': 'Notification not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f'Error marking notification as read: {str(e)}')
        return Response(
            {'error': 'Failed to mark notification as read'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    try:
        updated_count = Notification.objects.filter(
            recipient=request.user, 
            is_read=False
        ).update(is_read=True)
        
        logger.info(f'User {request.user.username} marked {updated_count} notifications as read')
        return Response({'message': f'{updated_count} notifications marked as read'})
    except Exception as e:
        logger.error(f'Error marking all notifications as read: {str(e)}')
        return Response(
            {'error': 'Failed to mark notifications as read'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_presence(request, username):
    """Get user's presence status"""
    try:
        user = User.objects.get(username=username)
        presence, created = UserPresence.objects.get_or_create(user=user)
        serializer = UserPresenceSerializer(presence)
        return Response(serializer.data)
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f'Error getting user presence: {str(e)}')
        return Response(
            {'error': 'Failed to get user presence'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_online_users(request):
    """Get list of online users"""
    try:
        online_users = User.objects.filter(
            userpresence__is_online=True
        ).exclude(id=request.user.id)
        
        serializer = UserSerializer(online_users, many=True)
        logger.info(f'User {request.user.username} retrieved {len(online_users)} online users')
        return Response(serializer.data)
    except Exception as e:
        logger.error(f'Error getting online users: {str(e)}')
        return Response(
            {'error': 'Failed to get online users'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )