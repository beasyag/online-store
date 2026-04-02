from django.db.models import Avg
from rest_framework import serializers

from products.models import Product

from .models import SellerProfile


class SellerProductSerializer(serializers.ModelSerializer):
    average_rating = serializers.FloatField(read_only=True, default=0)

    class Meta:
        model = Product
        fields = ("id", "name", "slug", "price", "old_price", "image_url", "stock", "is_active", "average_rating")


class SellerProfileSerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True, default=0)
    average_rating = serializers.FloatField(read_only=True, default=0)

    class Meta:
        model = SellerProfile
        fields = (
            "id",
            "shop_name",
            "description",
            "avatar",
            "created_at",
            "product_count",
            "average_rating",
        )


class SellerProfileDetailSerializer(SellerProfileSerializer):
    products = serializers.SerializerMethodField()

    class Meta(SellerProfileSerializer.Meta):
        fields = SellerProfileSerializer.Meta.fields + ("products",)

    def get_products(self, obj):
        products = (
            obj.products.filter(is_active=True)
            .select_related("category")
            .annotate(average_rating=Avg("reviews__rating"))
            .order_by("-created_at")[:8]
        )
        return SellerProductSerializer(products, many=True).data


class SellerProfileUpsertSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerProfile
        fields = ("shop_name", "description", "avatar")

