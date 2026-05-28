from django.conf import settings
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from favorites.models import Favorite
from products.models import Product
from products.serializers import ProductCardSerializer

from .services import (
    get_also_bought_products,
    get_recommendations_for_user,
    get_trending_products,
)


def _favorite_ids(request) -> set[int]:
    if request.user.is_authenticated:
        return set(Favorite.objects.filter(user=request.user).values_list("product_id", flat=True))
    return set()


class RecommendationsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if request.user.is_authenticated:
            products, strategy = get_recommendations_for_user(request.user, limit=12)
        else:
            cached_payload = cache.get("recommendations:anonymous:v1")
            if cached_payload is None:
                products, strategy = get_recommendations_for_user(request.user, limit=12)
                cached_payload = {"products": products, "strategy": strategy}
                cache.set("recommendations:anonymous:v1", cached_payload, timeout=settings.CACHE_TTL_PUBLIC_LISTS)
            products = cached_payload["products"]
            strategy = cached_payload["strategy"]

        serializer = ProductCardSerializer(
            products,
            many=True,
            context={"request": request, "favorite_ids": _favorite_ids(request)},
        )
        return Response({"strategy": strategy, "results": serializer.data})


class TrendingAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        cached = cache.get("recommendations:trending:v1")
        if cached is None:
            cached = get_trending_products(limit=12)
            cache.set("recommendations:trending:v1", cached, timeout=settings.CACHE_TTL_PUBLIC_LISTS)

        serializer = ProductCardSerializer(
            cached,
            many=True,
            context={"request": request, "favorite_ids": _favorite_ids(request)},
        )
        return Response({"results": serializer.data})


class AlsoBoughtAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        products = get_also_bought_products(product, limit=8)
        serializer = ProductCardSerializer(
            products,
            many=True,
            context={"request": request, "favorite_ids": _favorite_ids(request)},
        )
        return Response({"results": serializer.data})
