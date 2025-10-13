from django.urls import path
from .views import RegisterView, ProfileView, LogoutView, ChatRoomListCreateView, ChatRoomMessagesView, SendMessageView, JoinRoomView, LeaveRoomView

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
]