from rest_framework import serializers

from .models import ChatMessage, ChatRoom


class ChatMessageSerializer(serializers.ModelSerializer):
    author_display = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = ["id", "text", "author", "author_display", "created_at", "is_read"]
        read_only_fields = ["id", "author", "created_at", "is_read"]

    def get_author_display(self, obj) -> str:
        user = obj.author
        full = f"{user.first_name} {user.last_name}".strip()
        return full or user.username


class ChatRoomSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    other_party_name = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = ["id", "order", "buyer", "seller", "created_at", "last_message", "unread_count", "other_party_name"]
        read_only_fields = fields

    def get_last_message(self, obj):
        msg = obj.messages.order_by("-created_at").first()
        if msg:
            return {"text": msg.text[:80], "created_at": msg.created_at.isoformat()}
        return None

    def get_unread_count(self, obj) -> int:
        request = self.context.get("request")
        if not request:
            return 0
        return obj.messages.filter(is_read=False).exclude(author=request.user).count()

    def get_other_party_name(self, obj) -> str:
        request = self.context.get("request")
        if not request:
            return ""
        other = obj.seller if obj.buyer_id == request.user.id else obj.buyer
        full = f"{other.first_name} {other.last_name}".strip()
        return full or other.username
