from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from sellers.models import SellerProfile

User = get_user_model()


class SellerProfileInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerProfile
        fields = ("id", "shop_name", "description", "avatar")


class UserSerializer(serializers.ModelSerializer):
    seller_profile = SellerProfileInlineSerializer(read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "role", "first_name", "last_name", "seller_profile")


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    shop_name = serializers.CharField(write_only=True, required=False)
    shop_description = serializers.CharField(write_only=True, required=False, allow_blank=True)
    shop_avatar = serializers.URLField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password",
            "role",
            "first_name",
            "last_name",
            "shop_name",
            "shop_description",
            "shop_avatar",
        )

    def validate(self, attrs):
        role = attrs.get("role", User.Role.BUYER)
        if role == User.Role.SELLER and not attrs.get("shop_name"):
            raise serializers.ValidationError({"shop_name": "shop_name is required for seller registration."})
        return attrs

    def create(self, validated_data):
        shop_name = validated_data.pop("shop_name", "")
        shop_description = validated_data.pop("shop_description", "")
        shop_avatar = validated_data.pop("shop_avatar", "")

        user = User.objects.create_user(**validated_data)
        if user.role == User.Role.SELLER:
            SellerProfile.objects.create(
                user=user,
                shop_name=shop_name,
                description=shop_description,
                avatar=shop_avatar,
            )
        return user

    def to_representation(self, instance):
        return UserSerializer(instance, context=self.context).data


class MarketplaceTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data

