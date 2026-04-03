from django.conf import settings
from django.core.cache import cache
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from favorites.models import Favorite
from products.serializers import ProductCardSerializer

from .services import get_recommendations_for_user


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

        favorite_ids = set()
        if request.user.is_authenticated:
            favorite_ids = set(Favorite.objects.filter(user=request.user).values_list("product_id", flat=True))
        serializer = ProductCardSerializer(
            products,
            many=True,
            context={"request": request, "favorite_ids": favorite_ids},
        )
        return Response({"strategy": strategy, "results": serializer.data})
