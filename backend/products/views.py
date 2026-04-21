from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.db.models import DecimalField, ExpressionWrapper, F, Q
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from favorites.models import Favorite
from recommendations.services import get_similar_products
from users.models import User

from .models import Category, Product, ProductViewHistory, Tag
from .permissions import IsSellerOwnerOrReadOnly
from .serializers import (
    CategorySerializer,
    ProductCardSerializer,
    ProductDetailSerializer,
    ProductWriteSerializer,
    TagSerializer,
)
from .services import get_product_queryset


def _favorite_ids_for_user(user):
    if not user.is_authenticated:
        return set()
    return set(Favorite.objects.filter(user=user).values_list("product_id", flat=True))


def _cached_public_products(cache_key: str, fetcher):
    products = cache.get(cache_key)
    if products is None:
        products = list(fetcher())
        cache.set(cache_key, products, timeout=settings.CACHE_TTL_PUBLIC_LISTS)
    return products


class CategoryListAPIView(generics.ListAPIView):
    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    permission_classes = [AllowAny]


class TagListAPIView(generics.ListAPIView):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = [AllowAny]


class ProductListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsSellerOwnerOrReadOnly]

    def get_queryset(self):
        request = self.request
        user = request.user
        mine_only = request.query_params.get("mine") == "1"
        include_inactive = bool(
            user.is_authenticated and user.role in {User.Role.SELLER, User.Role.ADMIN} and mine_only
        )
        queryset = get_product_queryset(include_inactive=include_inactive, only_primary=not mine_only)

        if mine_only and hasattr(user, "seller_profile"):
            queryset = queryset.filter(seller=user.seller_profile)

        query = request.query_params.get("q")
        if query:
            search_vector = (
                SearchVector("name", weight="A", config="russian")
                + SearchVector("description", weight="B", config="russian")
                + SearchVector("tags__name", weight="B", config="russian")
                + SearchVector("category__name", weight="C", config="russian")
                + SearchVector("seller__shop_name", weight="C", config="russian")
            )
            search_query = SearchQuery(query, config="russian", search_type="websearch")
            queryset = (
                queryset
                .annotate(search=search_vector, rank=SearchRank(search_vector, search_query))
                .filter(Q(search=search_query) | Q(name__icontains=query))
                .order_by("-rank")
            )

        category = request.query_params.get("category")
        if category:
            if category.isdigit():
                queryset = queryset.filter(category_id=int(category))
            else:
                queryset = queryset.filter(category__slug=category)

        seller = request.query_params.get("seller")
        if seller and seller.isdigit():
            queryset = queryset.filter(seller_id=int(seller))

        tag = request.query_params.get("tag")
        if tag:
            if tag.isdigit():
                queryset = queryset.filter(tags__id=int(tag))
            else:
                queryset = queryset.filter(tags__slug=tag)

        min_price = request.query_params.get("min_price")
        if min_price:
            queryset = queryset.filter(price__gte=min_price)

        max_price = request.query_params.get("max_price")
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        ordering = request.query_params.get("ordering")
        ordering_map = {
            "price_asc": "price",
            "price_desc": "-price",
            "popular": "-purchases_count",
            "new": "-created_at",
            "rating": "-average_rating",
        }
        if ordering in ordering_map:
            queryset = queryset.order_by(ordering_map[ordering], "-created_at")
        else:
            queryset = queryset.order_by("-created_at")

        return queryset.distinct()

    def get_serializer_class(self):
        return ProductWriteSerializer if self.request.method == "POST" else ProductCardSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["favorite_ids"] = _favorite_ids_for_user(self.request.user)
        return context

    def list(self, request, *args, **kwargs):
        if request.method != "GET":
            return super().list(request, *args, **kwargs)
        return super().list(request, *args, **kwargs)


class ProductRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSellerOwnerOrReadOnly]

    def get_queryset(self):
        return get_product_queryset(include_inactive=True)

    def get_serializer_class(self):
        return ProductWriteSerializer if self.request.method in {"PUT", "PATCH"} else ProductDetailSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["favorite_ids"] = _favorite_ids_for_user(self.request.user)
        return context

    def get_object(self):
        obj = super().get_object()
        user = self.request.user
        can_manage = bool(
            user.is_authenticated
            and (user.role == User.Role.ADMIN or getattr(getattr(user, "seller_profile", None), "id", None) == obj.seller_id)
        )
        if not obj.is_active and not can_manage:
            raise Http404("Product does not exist.")
        return obj

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_active:
            Product.objects.filter(pk=instance.pk).update(views_count=F("views_count") + 1)
            instance.views_count += 1
        if request.user.is_authenticated:
            recent_view_threshold = timezone.now() - timedelta(minutes=settings.PRODUCT_VIEW_COOLDOWN_MINUTES)
            already_tracked_recently = ProductViewHistory.objects.filter(
                user=request.user,
                product=instance,
                viewed_at__gte=recent_view_threshold,
            ).exists()
            if not already_tracked_recently:
                ProductViewHistory.objects.create(user=request.user, product=instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class ProductSimilarAPIView(generics.ListAPIView):
    serializer_class = ProductCardSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        product = get_object_or_404(get_product_queryset(), pk=self.kwargs["pk"])
        return get_similar_products(product=product, limit=8)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["favorite_ids"] = _favorite_ids_for_user(self.request.user)
        return context


class ProductPopularAPIView(generics.ListAPIView):
    serializer_class = ProductCardSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return _cached_public_products(
            "products:popular:v1",
            lambda: get_product_queryset(only_primary=True).order_by("-purchases_count", "-views_count", "-average_rating")[:12],
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["favorite_ids"] = _favorite_ids_for_user(self.request.user)
        return context


class ProductDealsAPIView(generics.ListAPIView):
    serializer_class = ProductCardSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        def fetch():
            discount_amount = ExpressionWrapper(
                F("old_price") - F("price"),
                output_field=DecimalField(max_digits=10, decimal_places=2),
            )
            return (
                get_product_queryset(only_primary=True)
                .filter(old_price__isnull=False, old_price__gt=F("price"))
                .annotate(discount_amount=discount_amount)
                .order_by("-discount_amount", "-purchases_count", "-views_count")[:8]
            )

        return _cached_public_products(
            "products:deals:v1",
            fetch,
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["favorite_ids"] = _favorite_ids_for_user(self.request.user)
        return context


class ProductNewAPIView(generics.ListAPIView):
    serializer_class = ProductCardSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return _cached_public_products(
            "products:new:v1",
            lambda: get_product_queryset(only_primary=True).order_by("-created_at")[:12],
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["favorite_ids"] = _favorite_ids_for_user(self.request.user)
        return context
