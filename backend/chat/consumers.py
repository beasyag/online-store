import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model

from .models import ChatMessage, ChatRoom

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket-потребитель для чата.
    URL: ws://host/ws/chat/<room_id>/
    Аутентификация — через JWT-токен в query-параметре ?token=<access_token>
    """

    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"

        # Проверяем JWT и подгружаем пользователя
        user = await self._get_user_from_token()
        if user is None:
            await self.close(code=4001)
            return

        self.user = user

        # Проверяем, что пользователь является участником комнаты
        room = await self._get_room()
        if room is None:
            await self.close(code=4004)
            return

        self.room = room

        # Присоединяемся к группе channel layer
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Отправляем историю последних 50 сообщений
        history = await self._get_history()
        await self.send(text_data=json.dumps({"type": "history", "messages": history}))

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """Принимаем сообщение от WebSocket клиента."""
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        text = (data.get("text") or "").strip()[:2000]
        if not text:
            return

        # Сохраняем в БД
        message = await self._save_message(text)

        # Рассылаем всем участникам комнаты
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "id": message.id,
                "text": message.text,
                "author_id": self.user.id,
                "author_username": self.user.username,
                "author_display": self._display_name(self.user),
                "created_at": message.created_at.isoformat(),
            },
        )

    async def chat_message(self, event):
        """Обработчик события от channel layer — отправляет сообщение клиенту."""
        # Убираем внутренний type ('chat_message'), чтобы он не перезаписал наш 'message'
        payload = {k: v for k, v in event.items() if k != "type"}
        await self.send(text_data=json.dumps({"type": "message", **payload}))

    # ──────────────── Helpers ────────────────

    @staticmethod
    def _display_name(user) -> str:
        full = f"{user.first_name} {user.last_name}".strip()
        return full or user.username

    @database_sync_to_async
    def _get_user_from_token(self):
        """Валидируем JWT токен из query string."""
        try:
            from rest_framework_simplejwt.tokens import AccessToken

            query_string = self.scope.get("query_string", b"").decode()
            params = dict(p.split("=") for p in query_string.split("&") if "=" in p)
            token_str = params.get("token", "")
            if not token_str:
                return None

            token = AccessToken(token_str)
            return User.objects.get(id=token["user_id"])
        except Exception:
            return None

    @database_sync_to_async
    def _get_room(self):
        """Загружаем комнату и проверяем доступ."""
        try:
            room = ChatRoom.objects.select_related("buyer", "seller").get(pk=self.room_id)
            if self.user.id not in (room.buyer_id, room.seller_id):
                return None
            return room
        except ChatRoom.DoesNotExist:
            return None

    @database_sync_to_async
    def _get_history(self) -> list:
        messages = (
            ChatMessage.objects.filter(room=self.room)
            .select_related("author")
            .order_by("-created_at")[:50]
        )
        return [
            {
                "id": m.id,
                "text": m.text,
                "author": m.author_id,
                "author_username": m.author.username,
                "author_display": self._display_name(m.author),
                "created_at": m.created_at.isoformat(),
            }
            for m in reversed(list(messages))
        ]

    @database_sync_to_async
    def _save_message(self, text: str) -> ChatMessage:
        return ChatMessage.objects.create(room=self.room, author=self.user, text=text)
