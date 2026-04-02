from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from favorites.models import Favorite
from products.serializers import ProductCardSerializer

from .services import get_personalized_recommendations, has_personalization_signals


class RecommendationsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        products = get_personalized_recommendations(request.user, limit=12)
        favorite_ids = set()
        if request.user.is_authenticated:
            favorite_ids = set(Favorite.objects.filter(user=request.user).values_list("product_id", flat=True))
        serializer = ProductCardSerializer(
            products,
            many=True,
            context={"request": request, "favorite_ids": favorite_ids},
        )
        strategy = "personalized" if has_personalization_signals(request.user) else "popular_fallback"
        return Response({"strategy": strategy, "results": serializer.data})

