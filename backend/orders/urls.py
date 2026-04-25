from django.urls import path

from .views import (
    BranchListAPIView,
    OrderCreateAPIView,
    OrderDetailAPIView,
    OrderListAPIView,
    OrderStripeCheckoutAPIView,
    OrderStripeConfirmAPIView,
    SellerOrderDetailAPIView,
    SellerOrderListAPIView,
)

urlpatterns = [
    path("branches/", BranchListAPIView.as_view(), name="branch-list"),
    path("orders/create/", OrderCreateAPIView.as_view(), name="order-create"),
    path("orders/", OrderListAPIView.as_view(), name="order-list"),
    path("orders/checkout/confirm/", OrderStripeConfirmAPIView.as_view(), name="order-checkout-confirm"),
    path("orders/<int:pk>/checkout/", OrderStripeCheckoutAPIView.as_view(), name="order-checkout"),
    path("orders/<int:pk>/", OrderDetailAPIView.as_view(), name="order-detail"),
    path("orders/seller/", SellerOrderListAPIView.as_view(), name="seller-order-list"),
    path("orders/seller/<int:pk>/", SellerOrderDetailAPIView.as_view(), name="seller-order-detail"),
]
