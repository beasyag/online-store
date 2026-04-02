from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from products.models import Product

from .models import Favorite
from .serializers import FavoriteSerializer, FavoriteToggleSerializer


class FavoriteListAPIView(generics.ListAPIView):
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related(
            "product__category",
            "product__seller",
        )


class FavoriteToggleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FavoriteToggleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = get_object_or_404(Product.objects.filter(is_active=True), pk=serializer.validated_data["product_id"])
        favorite, created = Favorite.objects.get_or_create(user=request.user, product=product)
        if not created:
            favorite.delete()
            return Response({"status": "removed"}, status=status.HTTP_200_OK)
        return Response({"status": "added"}, status=status.HTTP_201_CREATED)

