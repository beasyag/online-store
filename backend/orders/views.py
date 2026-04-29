from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Branch, Order
from .serializers import (
    BranchSerializer,
    OrderCreateSerializer,
    OrderSerializer,
    SellerOrderSerializer,
    StripeCheckoutConfirmSerializer,
)
from .services import confirm_order_payment, create_checkout_session_for_order, create_order_from_cart


class BranchListAPIView(generics.ListAPIView):
    queryset = Branch.objects.filter(is_active=True)
    serializer_class = BranchSerializer
    permission_classes = []
    pagination_class = None  # Всегда возвращаем плоский список


class OrderCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = create_order_from_cart(
            request.user, 
            payment_method=serializer.validated_data["payment_method"],
            delivery_method=serializer.validated_data.get("delivery_method", Order.DeliveryMethod.COURIER),
            delivery_address=serializer.validated_data.get("delivery_address", ""),
            branch_id=serializer.validated_data.get("branch_id"),
        )
        
        # Запускаем фоновую задачу отправки уведомления в Celery
        from .tasks import process_order_notifications
        process_order_notifications.delay(order.id, request.user.email)
        
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


class OrderStripeCheckoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        order = Order.objects.filter(user=request.user).prefetch_related("items__product").get(pk=pk)
        session = create_checkout_session_for_order(order)
        return Response({"checkout_url": session.url}, status=status.HTTP_200_OK)


class OrderStripeConfirmAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = StripeCheckoutConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = confirm_order_payment(request.user, serializer.validated_data["session_id"])
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)


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
