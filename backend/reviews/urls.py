from django.urls import path

from .views import ProductReviewListCreateAPIView

urlpatterns = [
    path("products/<int:product_id>/reviews/", ProductReviewListCreateAPIView.as_view(), name="product-reviews"),
]

