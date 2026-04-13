from django.urls import path

from .views import (
    GoogleAuthAPIView,
    MarketplaceTokenObtainPairView,
    MarketplaceTokenRefreshView,
    ProfileAPIView,
    RegisterAPIView,
)

urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="auth-register"),
    path("login/", MarketplaceTokenObtainPairView.as_view(), name="auth-login"),
    path("google/", GoogleAuthAPIView.as_view(), name="auth-google"),
    path("refresh/", MarketplaceTokenRefreshView.as_view(), name="auth-refresh"),
    path("profile/", ProfileAPIView.as_view(), name="auth-profile"),
]
