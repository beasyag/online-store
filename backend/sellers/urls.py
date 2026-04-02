from django.urls import path

from .views import (
    CurrentSellerProfileAPIView,
    SellerDashboardAPIView,
    SellerDetailAPIView,
    SellerListAPIView,
    SellerProductsAPIView,
)

urlpatterns = [
    path("sellers/", SellerListAPIView.as_view(), name="seller-list"),
    path("sellers/<int:pk>/", SellerDetailAPIView.as_view(), name="seller-detail"),
    path("sellers/<int:pk>/products/", SellerProductsAPIView.as_view(), name="seller-products"),
    path("seller/profile/", CurrentSellerProfileAPIView.as_view(), name="seller-profile"),
    path("seller/dashboard/", SellerDashboardAPIView.as_view(), name="seller-dashboard"),
]

