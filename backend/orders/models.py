from django.conf import settings
from django.db import models


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        COMPLETED = "completed", "Completed"
        CANCELED = "canceled", "Canceled"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Order #{self.pk}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        related_name="order_items",
        null=True,
        blank=True,
    )
    seller = models.ForeignKey(
        "sellers.SellerProfile",
        on_delete=models.SET_NULL,
        related_name="order_items",
        null=True,
        blank=True,
    )
    quantity = models.PositiveIntegerField(default=1)
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self) -> str:
        return f"Order item #{self.pk}"

