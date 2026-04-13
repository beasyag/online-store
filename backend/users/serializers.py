from django.conf import settings
from django.contrib.auth import get_user_model
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

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


def build_auth_response(user):
    refresh = RefreshToken.for_user(user)
    refresh["role"] = user.role
    access = refresh.access_token
    access["role"] = user.role
    return {
        "access": str(access),
        "refresh": str(refresh),
        "user": UserSerializer(user).data,
    }


class GoogleAuthSerializer(serializers.Serializer):
    credential = serializers.CharField()

    default_error_messages = {
        "google_not_configured": "Google sign-in is not configured.",
        "invalid_token": "Invalid Google credential.",
        "email_not_verified": "Google account email is not verified.",
    }

    def validate(self, attrs):
        if not settings.GOOGLE_CLIENT_ID:
            self.fail("google_not_configured")

        try:
            with urlopen(
                f"https://oauth2.googleapis.com/tokeninfo?{urlencode({'id_token': attrs['credential']})}",
                timeout=10,
            ) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, json.JSONDecodeError) as error:
            raise serializers.ValidationError({"credential": self.error_messages["invalid_token"]}) from error

        audience = payload.get("aud")
        if audience != settings.GOOGLE_CLIENT_ID:
            raise serializers.ValidationError({"credential": self.error_messages["invalid_token"]})

        if str(payload.get("email_verified", "")).lower() != "true":
            raise serializers.ValidationError({"credential": self.error_messages["email_not_verified"]})

        attrs["google_payload"] = payload
        return attrs

    def create(self, validated_data):
        payload = validated_data["google_payload"]
        email = payload["email"].strip().lower()
        google_sub = payload["sub"]

        user = User.objects.filter(google_sub=google_sub).first()
        if not user:
            user = User.objects.filter(email__iexact=email).first()

        if not user:
            base_username = (email.split("@", 1)[0] or "google-user")[:150]
            username = base_username
            suffix = 1
            while User.objects.filter(username=username).exists():
                suffix_text = str(suffix)
                username = f"{base_username[: 150 - len(suffix_text) - 1]}-{suffix_text}"
                suffix += 1

            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=payload.get("given_name", "")[:150],
                last_name=payload.get("family_name", "")[:150],
                password=None,
            )

        updated_fields = []
        if user.google_sub != google_sub:
            user.google_sub = google_sub
            updated_fields.append("google_sub")
        if not user.first_name and payload.get("given_name"):
            user.first_name = payload["given_name"][:150]
            updated_fields.append("first_name")
        if not user.last_name and payload.get("family_name"):
            user.last_name = payload["family_name"][:150]
            updated_fields.append("last_name")
        if user.email != email:
            user.email = email
            updated_fields.append("email")

        if updated_fields:
            user.save(update_fields=updated_fields)

        return user
