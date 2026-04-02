from rest_framework import serializers

from products.serializers import ProductSummarySerializer

from .models import Favorite


class FavoriteSerializer(serializers.ModelSerializer):
    product = ProductSummarySerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ("id", "created_at", "product")


class FavoriteToggleSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()

