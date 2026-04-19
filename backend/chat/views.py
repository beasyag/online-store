from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ChatMessage, ChatRoom
from .serializers import ChatMessageSerializer, ChatRoomSerializer


class MyRoomsListView(generics.ListAPIView):
    """GET /api/chat/rooms/ — список комнат текущего пользователя."""

    serializer_class = ChatRoomSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        return (
            ChatRoom.objects.filter(buyer=user)
            | ChatRoom.objects.filter(seller=user)
        ).prefetch_related("messages").order_by("-created_at")


class RoomCreateView(APIView):
    """POST /api/chat/rooms/ — создать или вернуть существующую комнату."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        seller_id = request.data.get("seller_id")
        order_id = request.data.get("order_id")  # необязательно

        if not seller_id:
            return Response({"detail": "seller_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            seller_user = User.objects.get(pk=seller_id)
        except User.DoesNotExist:
            return Response({"detail": "Seller not found."}, status=status.HTTP_404_NOT_FOUND)

        room, _ = ChatRoom.objects.get_or_create(
            buyer=request.user,
            seller=seller_user,
            order_id=order_id or None,
        )
        return Response(ChatRoomSerializer(room, context={"request": request}).data, status=status.HTTP_200_OK)


class RoomHistoryView(generics.ListAPIView):
    """GET /api/chat/rooms/<room_id>/messages/ — история сообщений."""

    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        room_id = self.kwargs["room_id"]
        user = self.request.user
        room = ChatRoom.objects.filter(pk=room_id).filter(
            buyer=user
        ).first() or ChatRoom.objects.filter(pk=room_id, seller=user).first()

        if not room:
            return ChatMessage.objects.none()

        # Помечаем как прочитанные
        room.messages.exclude(author=user).filter(is_read=False).update(is_read=True)
        return room.messages.select_related("author").order_by("created_at")
