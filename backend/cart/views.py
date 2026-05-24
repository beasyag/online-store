from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from products.models import Product

from .models import CartItem
from .serializers import AddToCartSerializer, CartSerializer, UpdateCartItemSerializer
from .services import get_or_create_cart


class CartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = get_or_create_cart(request.user)
        cart = cart.__class__.objects.prefetch_related("items__product__category", "items__product__seller").get(pk=cart.pk)
        return Response(CartSerializer(cart).data)


class CartAddAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart = get_or_create_cart(request.user)
        product = get_object_or_404(Product.objects.filter(is_active=True), pk=serializer.validated_data["product_id"])
        quantity = serializer.validated_data["quantity"]

        cart_item = CartItem.objects.filter(cart=cart, product=product).first()
        current_quantity = cart_item.quantity if cart_item else 0

        if current_quantity + quantity > product.stock:
            return Response({"detail": "Недостаточно товара на складе."}, status=status.HTTP_400_BAD_REQUEST)

        if cart_item:
            cart_item.quantity += quantity
            cart_item.save(update_fields=["quantity"])
        else:
            CartItem.objects.create(cart=cart, product=product, quantity=quantity)

        cart.refresh_from_db()
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)


class CartItemAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart = get_or_create_cart(request.user)
        item = get_object_or_404(CartItem.objects.select_related("product"), pk=pk, cart=cart)
        if serializer.validated_data["quantity"] > item.product.stock:
            return Response({"detail": "Недостаточно товара на складе."}, status=status.HTTP_400_BAD_REQUEST)
        item.quantity = serializer.validated_data["quantity"]
        item.save(update_fields=["quantity"])
        cart.refresh_from_db()
        return Response(CartSerializer(cart).data)

    def delete(self, request, pk):
        cart = get_or_create_cart(request.user)
        item = get_object_or_404(CartItem, pk=pk, cart=cart)
        item.delete()
        cart.refresh_from_db()
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)

