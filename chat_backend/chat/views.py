from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, UserSerializer, ChatRoomSerializer, ChatMessageSerializer, UserRoomSerializer
from .models import ChatRoom, ChatMessage, UserRoom


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