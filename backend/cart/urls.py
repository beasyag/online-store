from django.urls import path

from .views import CartAPIView, CartAddAPIView, CartItemAPIView

urlpatterns = [
    path("cart/", CartAPIView.as_view(), name="cart-detail"),
    path("cart/add/", CartAddAPIView.as_view(), name="cart-add"),
    path("cart/item/<int:pk>/", CartItemAPIView.as_view(), name="cart-item"),
]

