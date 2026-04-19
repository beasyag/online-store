from django.urls import path

from .views import MyRoomsListView, RoomCreateView, RoomHistoryView

urlpatterns = [
    path("chat/rooms/", RoomCreateView.as_view(), name="chat-room-create"),
    path("chat/rooms/list/", MyRoomsListView.as_view(), name="chat-room-list"),
    path("chat/rooms/<int:room_id>/messages/", RoomHistoryView.as_view(), name="chat-room-history"),
]
