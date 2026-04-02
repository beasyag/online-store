from rest_framework import serializers

from sellers.models import SellerProfile

from .models import Category, Product, Tag
from .services import discount_percent, get_product_queryset


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug")


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "slug")


class SellerMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerProfile
        fields = ("id", "shop_name", "avatar")


class ProductSummarySerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    seller = SellerMiniSerializer(read_only=True)
    average_rating = serializers.FloatField(read_only=True, default=0)
    reviews_count = serializers.IntegerField(read_only=True, default=0)
    discount_percent = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "offer_group",
            "price",
            "old_price",
            "discount_percent",
            "image_url",
            "stock",
            "category",
            "seller",
            "average_rating",
            "reviews_count",
        )

    def get_discount_percent(self, obj):
        return discount_percent(obj)


class ProductCardSerializer(ProductSummarySerializer):
    tags = TagSerializer(read_only=True, many=True)
    is_favorite = serializers.SerializerMethodField()

    class Meta(ProductSummarySerializer.Meta):
        fields = ProductSummarySerializer.Meta.fields + (
            "tags",
            "views_count",
            "purchases_count",
            "created_at",
            "is_favorite",
        )

    def get_is_favorite(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        favorite_ids = self.context.get("favorite_ids")
        if favorite_ids is not None:
            return obj.id in favorite_ids
        return obj.favorited_by.filter(user=request.user).exists()


class ProductDetailSerializer(ProductCardSerializer):
    seller_offers = serializers.SerializerMethodField()

    class Meta(ProductCardSerializer.Meta):
        fields = ProductCardSerializer.Meta.fields + ("description", "is_active", "updated_at", "seller_offers")

    def get_seller_offers(self, obj):
        request = self.context.get("request")
        can_manage = bool(
            request
            and request.user.is_authenticated
            and (
                request.user.role == request.user.Role.ADMIN
                or getattr(getattr(request.user, "seller_profile", None), "id", None) == obj.seller_id
            )
        )
        queryset = get_product_queryset(include_inactive=can_manage).filter(offer_group=obj.offer_group)
        if not can_manage:
            queryset = queryset.filter(is_active=True)
        offers = list(queryset.order_by("price", "-average_rating", "-purchases_count", "seller__shop_name"))
        return ProductSummarySerializer(offers, many=True, context=self.context).data


class ProductWriteSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(source="category", queryset=Category.objects.all())
    tag_ids = serializers.PrimaryKeyRelatedField(source="tags", queryset=Tag.objects.all(), many=True, required=False)

    class Meta:
        model = Product
        fields = (
            "id",
            "category_id",
            "name",
            "offer_group",
            "description",
            "price",
            "old_price",
            "image_url",
            "stock",
            "is_active",
            "tag_ids",
        )

    def validate(self, attrs):
        price = attrs.get("price", getattr(self.instance, "price", None))
        old_price = attrs.get("old_price", getattr(self.instance, "old_price", None))
        if old_price is not None and price is not None and old_price <= price:
            raise serializers.ValidationError({"old_price": "old_price must be greater than current price."})
        return attrs

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        seller = getattr(self.context["request"].user, "seller_profile", None)
        if not seller:
            raise serializers.ValidationError("Seller profile is required to create a product.")
        product = Product.objects.create(seller=seller, **validated_data)
        if tags:
            product.tags.set(tags)
        return product

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tags is not None:
            instance.tags.set(tags)
        return instance

    def to_representation(self, instance):
        return ProductDetailSerializer(instance, context=self.context).data
