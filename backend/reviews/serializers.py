from rest_framework import serializers

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ("id", "user", "rating", "text", "created_at")

    def get_user(self, obj):
        return {"id": obj.user_id, "username": obj.user.username}


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ("rating", "text")

