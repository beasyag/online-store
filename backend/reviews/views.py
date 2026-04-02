from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated

from products.models import Product

from .models import Review
from .serializers import ReviewCreateSerializer, ReviewSerializer


class ProductReviewListCreateAPIView(generics.ListCreateAPIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        return Review.objects.filter(product_id=self.kwargs["product_id"]).select_related("user")

    def get_serializer_class(self):
        return ReviewCreateSerializer if self.request.method == "POST" else ReviewSerializer

    def perform_create(self, serializer):
        product = generics.get_object_or_404(Product, pk=self.kwargs["product_id"], is_active=True)
        if Review.objects.filter(user=self.request.user, product=product).exists():
            raise ValidationError({"detail": "You have already reviewed this product."})
        serializer.save(user=self.request.user, product=product)

