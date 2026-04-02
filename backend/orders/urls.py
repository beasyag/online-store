from django.urls import path

from .views import (
    OrderCreateAPIView,
    OrderDetailAPIView,
    OrderListAPIView,
    SellerOrderDetailAPIView,
    SellerOrderListAPIView,
)

urlpatterns = [
    path("orders/create/", OrderCreateAPIView.as_view(), name="order-create"),
    path("orders/", OrderListAPIView.as_view(), name="order-list"),
    path("orders/<int:pk>/", OrderDetailAPIView.as_view(), name="order-detail"),
    path("orders/seller/", SellerOrderListAPIView.as_view(), name="seller-order-list"),
    path("orders/seller/<int:pk>/", SellerOrderDetailAPIView.as_view(), name="seller-order-detail"),
]

