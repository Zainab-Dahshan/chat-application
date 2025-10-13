from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password
from .models import ChatRoom, ChatMessage, UserRoom, Notification, UserPresence


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'date_joined')
        read_only_fields = ('id', 'date_joined')


class ChatRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = ['id', 'name', 'created_at']


class ChatMessageSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'room', 'user', 'username', 'message', 'message_type', 'file', 'file_url', 'file_name', 'file_size', 'mime_type', 'timestamp']
        read_only_fields = ['id', 'timestamp', 'room', 'user', 'file_url', 'file_name', 'file_size', 'mime_type']
        extra_kwargs = {
            'file': {'write_only': True, 'required': False},
            'message': {'required': False}
        }
    
    def get_file_url(self, obj):
        """Get the full URL for the file"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def validate(self, data):
        """Validate that either message or file is provided"""
        message = data.get('message')
        file = data.get('file')
        message_type = data.get('message_type', 'text')
        
        if message_type == 'text' and not message:
            raise serializers.ValidationError({"message": "Message content is required for text messages"})
        
        if message_type != 'text' and not file:
            raise serializers.ValidationError({"file": "File is required for non-text messages"})
        
        if message and len(message) > 1000:
            raise serializers.ValidationError({"message": "Message too long (max 1000 characters)"})
        
        return data
    
    def create(self, validated_data):
        """Create message with file handling"""
        file = validated_data.pop('file', None)
        message = super().create(validated_data)
        
        if file:
            # Set file metadata
            message.file_name = file.name
            message.file_size = file.size
            
            # Try to detect MIME type
            import mimetypes
            mime_type, _ = mimetypes.guess_type(file.name)
            if mime_type:
                message.mime_type = mime_type
            
            message.save()
        
        return message


class UserRoomSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)
    
    class Meta:
        model = UserRoom
        fields = ['id', 'user', 'username', 'room', 'room_name', 'joined_at']
        read_only_fields = ['id', 'joined_at']


class NotificationSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    
    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'title', 'message', 'is_read', 'sender_username', 'room_name', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserPresenceSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserPresence
        fields = ['username', 'is_online', 'last_seen', 'current_room']