from decimal import Decimal

from rest_framework import serializers

from .models import Branch, Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    seller = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ("id", "product", "seller", "quantity", "price_at_purchase", "subtotal")

    def get_product(self, obj):
        if not obj.product:
            return {"id": None, "name": "Deleted product"}
        return {
            "id": obj.product_id,
            "name": obj.product.name,
            "image_url": obj.product.image_url,
        }

    def get_seller(self, obj):
        if not obj.seller:
            return {"id": None, "shop_name": "Unknown seller"}
        return {"id": obj.seller_id, "shop_name": obj.seller.shop_name}

    def get_subtotal(self, obj):
        return Decimal(obj.price_at_purchase) * obj.quantity


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ("id", "name", "city", "address", "latitude", "longitude", "working_hours")


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    branch = BranchSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ("id", "status", "payment_method", "delivery_method", "delivery_address", "branch", "total_amount", "created_at", "updated_at", "items")


class OrderCreateSerializer(serializers.Serializer):
    payment_method = serializers.ChoiceField(choices=Order.PaymentMethod.choices)
    delivery_method = serializers.ChoiceField(choices=Order.DeliveryMethod.choices, default=Order.DeliveryMethod.COURIER)
    delivery_address = serializers.CharField(max_length=500, required=False, allow_blank=True)
    branch_id = serializers.IntegerField(required=False, allow_null=True)


class StripeCheckoutSessionSerializer(serializers.Serializer):
    checkout_url = serializers.URLField(read_only=True)


class StripeCheckoutConfirmSerializer(serializers.Serializer):
    session_id = serializers.CharField()


class SellerOrderSerializer(OrderSerializer):
    items = serializers.SerializerMethodField()
    seller_total = serializers.SerializerMethodField()

    class Meta(OrderSerializer.Meta):
        fields = OrderSerializer.Meta.fields + ("seller_total",)

    def get_items(self, obj):
        seller = self.context["seller"]
        items = obj.items.filter(seller=seller)
        return OrderItemSerializer(items, many=True).data

    def get_seller_total(self, obj):
        seller = self.context["seller"]
        return sum(Decimal(item.price_at_purchase) * item.quantity for item in obj.items.filter(seller=seller))
