from rest_framework.permissions import BasePermission

from users.models import User


class IsSellerUser(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role in {User.Role.SELLER, User.Role.ADMIN})

