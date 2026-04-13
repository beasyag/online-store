from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import (
    GoogleAuthSerializer,
    MarketplaceTokenObtainPairSerializer,
    RegisterSerializer,
    UserSerializer,
    build_auth_response,
)


class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class MarketplaceTokenObtainPairView(TokenObtainPairView):
    serializer_class = MarketplaceTokenObtainPairSerializer


class ProfileAPIView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class MarketplaceTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]


class GoogleAuthAPIView(generics.GenericAPIView):
    serializer_class = GoogleAuthSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(build_auth_response(user), status=status.HTTP_200_OK)
