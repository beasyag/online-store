from rest_framework.permissions import SAFE_METHODS, BasePermission

from users.models import User


class IsSellerOwnerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return bool(user and user.is_authenticated and user.role in {User.Role.SELLER, User.Role.ADMIN})

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if user.role == User.Role.ADMIN:
            return True
        seller_profile = getattr(user, "seller_profile", None)
        return bool(seller_profile and obj.seller_id == seller_profile.id)

