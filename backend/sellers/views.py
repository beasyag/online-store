from decimal import Decimal

from django.db.models import Avg, Count, DecimalField, ExpressionWrapper, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import OrderItem
from products.serializers import ProductCardSerializer
from products.services import get_product_queryset
from users.models import User

from .models import SellerProfile
from .permissions import IsSellerUser
from .serializers import SellerProfileDetailSerializer, SellerProfileSerializer, SellerProfileUpsertSerializer


class SellerListAPIView(generics.ListAPIView):
    serializer_class = SellerProfileSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return SellerProfile.objects.annotate(
            product_count=Count("products", filter=Q(products__is_active=True), distinct=True),
            average_rating=Coalesce(Avg("products__reviews__rating"), Value(0.0)),
        ).select_related("user")


class SellerDetailAPIView(generics.RetrieveAPIView):
    serializer_class = SellerProfileDetailSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return SellerProfile.objects.annotate(
            product_count=Count("products", filter=Q(products__is_active=True), distinct=True),
            average_rating=Coalesce(Avg("products__reviews__rating"), Value(0.0)),
        ).select_related("user")


class SellerProductsAPIView(generics.ListAPIView):
    serializer_class = ProductCardSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return get_product_queryset().filter(seller_id=self.kwargs["pk"])


class CurrentSellerProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        seller = getattr(request.user, "seller_profile", None)
        if not seller:
            raise NotFound("Seller profile does not exist.")
        serializer = SellerProfileDetailSerializer(seller, context={"request": request})
        return Response(serializer.data)

    def post(self, request):
        if hasattr(request.user, "seller_profile"):
            raise PermissionDenied("Seller profile already exists.")

        serializer = SellerProfileUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.role = User.Role.SELLER
        request.user.save(update_fields=["role"])
        seller = SellerProfile.objects.create(user=request.user, **serializer.validated_data)
        return Response(
            SellerProfileDetailSerializer(seller, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    def put(self, request):
        return self._update(request, partial=False)

    def patch(self, request):
        return self._update(request, partial=True)

    def _update(self, request, partial: bool):
        seller = getattr(request.user, "seller_profile", None)
        if not seller:
            raise NotFound("Seller profile does not exist.")
        serializer = SellerProfileUpsertSerializer(seller, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(SellerProfileDetailSerializer(seller, context={"request": request}).data)


class SellerDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSellerUser]

    def get(self, request):
        seller = getattr(request.user, "seller_profile", None)
        if not seller:
            raise NotFound("Seller profile does not exist.")

        order_items = OrderItem.objects.filter(seller=seller).select_related("order", "product")
        total_sales = order_items.aggregate(
            total=Coalesce(
                Sum(
                    ExpressionWrapper(
                        F("quantity") * F("price_at_purchase"),
                        output_field=DecimalField(max_digits=12, decimal_places=2),
                    )
                ),
                Value(Decimal("0.00")),
            )
        )["total"]
        top_products = get_product_queryset(include_inactive=True).filter(seller=seller).order_by(
            "-purchases_count",
            "-views_count",
        )[:5]
        recent_items = order_items.order_by("-order__created_at")[:8]

        data = {
            "product_count": seller.products.count(),
            "orders_count": order_items.values("order_id").distinct().count(),
            "sales_count": order_items.aggregate(total=Coalesce(Sum("quantity"), 0))["total"],
            "total_sales": total_sales,
            "top_products": ProductCardSerializer(top_products, many=True, context={"request": request}).data,
            "recent_orders": [
                {
                    "order_id": item.order_id,
                    "created_at": item.order.created_at,
                    "status": item.order.status,
                    "quantity": item.quantity,
                    "price_at_purchase": item.price_at_purchase,
                    "product": {
                        "id": item.product_id,
                        "name": item.product.name if item.product else "Deleted product",
                    },
                }
                for item in recent_items
            ],
        }
        return Response(data)

