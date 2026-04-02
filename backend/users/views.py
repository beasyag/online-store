from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import MarketplaceTokenObtainPairSerializer, RegisterSerializer, UserSerializer


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

