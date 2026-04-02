from django.urls import path

from .views import (
    CategoryListAPIView,
    ProductDealsAPIView,
    ProductListCreateAPIView,
    ProductNewAPIView,
    ProductPopularAPIView,
    ProductRetrieveUpdateDestroyAPIView,
    ProductSimilarAPIView,
    TagListAPIView,
)

urlpatterns = [
    path("categories/", CategoryListAPIView.as_view(), name="category-list"),
    path("tags/", TagListAPIView.as_view(), name="tag-list"),
    path("products/", ProductListCreateAPIView.as_view(), name="product-list"),
    path("products/deals/", ProductDealsAPIView.as_view(), name="product-deals"),
    path("products/new/", ProductNewAPIView.as_view(), name="product-new"),
    path("products/popular/", ProductPopularAPIView.as_view(), name="product-popular"),
    path("products/<int:pk>/", ProductRetrieveUpdateDestroyAPIView.as_view(), name="product-detail"),
    path("products/<int:pk>/similar/", ProductSimilarAPIView.as_view(), name="product-similar"),
]
