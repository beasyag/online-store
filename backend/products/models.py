from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.text import slugify

from common.utils import build_unique_slug


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=255, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_unique_slug(Category, self.name, instance=self)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=255, unique=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_unique_slug(Tag, self.name, instance=self)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class ProductQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def primary(self):
        return self.filter(is_primary_offer=True)


class Product(models.Model):
    seller = models.ForeignKey("sellers.SellerProfile", on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    offer_group = models.SlugField(max_length=140, db_index=True, blank=True)
    is_primary_offer = models.BooleanField(default=False, db_index=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image_url = models.URLField(blank=True)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField(Tag, related_name="products", blank=True)
    views_count = models.PositiveIntegerField(default=0)
    purchases_count = models.PositiveIntegerField(default=0)

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active", "-created_at"]),
            models.Index(fields=["category", "price"]),
            models.Index(fields=["seller", "is_active"]),
            models.Index(fields=["offer_group", "is_active"]),
            models.Index(fields=["offer_group", "is_primary_offer", "is_active"]),
        ]

    def save(self, *args, **kwargs):
        previous_offer_group = None
        if self.pk:
            previous_offer_group = Product.objects.filter(pk=self.pk).values_list("offer_group", flat=True).first()
        if not self.slug:
            self.slug = build_unique_slug(Product, self.name, instance=self)
        if not self.offer_group and self.name and self.category_id:
            category_slug = getattr(self.category, "slug", "") or "catalog"
            self.offer_group = slugify(f"{category_slug}-{self.name}")[:140] or self.slug
        if self.old_price is not None and self.old_price <= Decimal("0"):
            self.old_price = None
        super().save(*args, **kwargs)
        refresh_primary_offer_for_group(self.offer_group)
        if previous_offer_group and previous_offer_group != self.offer_group:
            refresh_primary_offer_for_group(previous_offer_group)

    def delete(self, *args, **kwargs):
        offer_group = self.offer_group
        super().delete(*args, **kwargs)
        refresh_primary_offer_for_group(offer_group)

    def __str__(self) -> str:
        return self.name


def refresh_primary_offer_for_group(offer_group: str):
    if not offer_group:
        return

    candidates = Product.objects.filter(offer_group=offer_group).order_by(
        "-is_active",
        "price",
        "-purchases_count",
        "-views_count",
        "created_at",
        "pk",
    )
    primary_id = candidates.values_list("id", flat=True).first()
    Product.objects.filter(offer_group=offer_group).exclude(pk=primary_id).update(is_primary_offer=False)
    if primary_id is not None:
        Product.objects.filter(pk=primary_id).update(is_primary_offer=True)


class ProductViewHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="product_views")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="view_history")
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-viewed_at"]
        indexes = [
            models.Index(fields=["user", "-viewed_at"]),
            models.Index(fields=["product", "-viewed_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} viewed {self.product}"
