from decimal import Decimal

from rest_framework import serializers

from products.serializers import ProductSummarySerializer

from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSummarySerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ("id", "product", "quantity", "subtotal")

    def get_subtotal(self, obj):
        return Decimal(obj.product.price) * obj.quantity


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ("id", "created_at", "updated_at", "total_items", "total_amount", "items")

    def get_total_items(self, obj):
        return sum(item.quantity for item in obj.items.all())

    def get_total_amount(self, obj):
        total = Decimal("0.00")
        for item in obj.items.select_related("product").all():
            total += Decimal(item.product.price) * item.quantity
        return total


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)

