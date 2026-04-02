from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order
from .serializers import OrderSerializer, SellerOrderSerializer
from .services import create_order_from_cart


class OrderCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order = create_order_from_cart(request.user)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderListAPIView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related("items__product", "items__seller")


class OrderDetailAPIView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related("items__product", "items__seller")


class SellerOrderListAPIView(generics.ListAPIView):
    serializer_class = SellerOrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        seller = getattr(self.request.user, "seller_profile", None)
        if not seller:
            raise PermissionDenied("Seller profile is required.")
        return (
            Order.objects.filter(items__seller=seller)
            .distinct()
            .prefetch_related("items__product", "items__seller")
            .order_by("-created_at")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["seller"] = self.request.user.seller_profile
        return context


class SellerOrderDetailAPIView(generics.RetrieveAPIView):
    serializer_class = SellerOrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        seller = getattr(self.request.user, "seller_profile", None)
        if not seller:
            raise PermissionDenied("Seller profile is required.")
        return Order.objects.filter(items__seller=seller).distinct().prefetch_related("items__product", "items__seller")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["seller"] = self.request.user.seller_profile
        return context

