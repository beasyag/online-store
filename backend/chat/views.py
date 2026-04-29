from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ChatMessage, ChatRoom
from .serializers import ChatMessageSerializer, ChatRoomSerializer


class MyRoomsListView(generics.ListAPIView):
    """GET /api/chat/rooms/ — список комнат текущего пользователя (только с сообщениями)."""

    serializer_class = ChatRoomSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        return (
            ChatRoom.objects.filter(buyer=user)
            | ChatRoom.objects.filter(seller=user)
        ).filter(
            messages__isnull=False  # только комнаты с хотя бы одним сообщением
        ).distinct().prefetch_related("messages").order_by("-created_at")


class RoomCreateView(APIView):
    """
    GET  /api/chat/rooms/?seller_id=X — найти существующую комнату (без создания).
    POST /api/chat/rooms/             — создать комнату (только при отправке первого сообщения).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Найти существующую комнату с продавцом. Если нет — 404 (комната НЕ создаётся)."""
        from sellers.models import SellerProfile
        seller_id = request.query_params.get("seller_id")
        if not seller_id:
            return Response({"detail": "seller_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            seller_profile = SellerProfile.objects.select_related("user").get(pk=seller_id)
        except SellerProfile.DoesNotExist:
            return Response({"detail": "Seller not found."}, status=status.HTTP_404_NOT_FOUND)

        room = ChatRoom.objects.filter(buyer=request.user, seller=seller_profile.user).first()
        if not room:
            return Response({"detail": "Room not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ChatRoomSerializer(room, context={"request": request}).data)

    def post(self, request):
        """Создать или вернуть существующую комнату. Вызывается только при отправке первого сообщения."""
        from sellers.models import SellerProfile

        seller_id = request.data.get("seller_id")
        order_id = request.data.get("order_id")

        if not seller_id:
            return Response({"detail": "seller_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            seller_profile = SellerProfile.objects.select_related("user").get(pk=seller_id)
            seller_user = seller_profile.user
        except SellerProfile.DoesNotExist:
            return Response({"detail": "Seller not found."}, status=status.HTTP_404_NOT_FOUND)

        if seller_user == request.user:
            return Response({"detail": "Cannot create chat with yourself."}, status=status.HTTP_400_BAD_REQUEST)

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
    pagination_class = None

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
