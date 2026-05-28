from django.urls import path

from .views import AlsoBoughtAPIView, RecommendationsAPIView, TrendingAPIView

urlpatterns = [
    path("recommendations/", RecommendationsAPIView.as_view(), name="recommendations"),
    path("recommendations/trending/", TrendingAPIView.as_view(), name="recommendations-trending"),
    path("products/<int:pk>/also-bought/", AlsoBoughtAPIView.as_view(), name="product-also-bought"),
]
