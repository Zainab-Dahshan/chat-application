from django.urls import path
from .views import (
    RegisterView, ProfileView, LogoutView, 
    ChatRoomListCreateView, ChatRoomMessagesView, SendMessageView, JoinRoomView, LeaveRoomView,
    get_notifications, mark_notification_read, mark_all_notifications_read, get_user_presence, get_online_users
)

app_name = 'chat'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Chat room endpoints
    path('rooms/', ChatRoomListCreateView.as_view(), name='room-list-create'),
    path('rooms/<int:room_id>/messages/', ChatRoomMessagesView.as_view(), name='room-messages'),
    path('rooms/<int:room_id>/send-message/', SendMessageView.as_view(), name='send-message'),
    path('rooms/<int:room_id>/join/', JoinRoomView.as_view(), name='join-room'),
    path('rooms/<int:room_id>/leave/', LeaveRoomView.as_view(), name='leave-room'),
    
    # Notification endpoints
    path('notifications/', get_notifications, name='get-notifications'),
    path('notifications/<int:notification_id>/mark-read/', mark_notification_read, name='mark-notification-read'),
    path('notifications/mark-all-read/', mark_all_notifications_read, name='mark-all-notifications-read'),
    
    # User presence endpoints
    path('users/<str:username>/presence/', get_user_presence, name='get-user-presence'),
    path('users/online/', get_online_users, name='get-online-users'),
]