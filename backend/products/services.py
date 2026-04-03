from decimal import Decimal

from django.db.models import Avg, Count, Value
from django.db.models.functions import Coalesce

from .models import Product


def get_product_queryset(include_inactive: bool = False, include_tags: bool = True, only_primary: bool = False):
    queryset = Product.objects.select_related("seller", "category").annotate(
        average_rating=Coalesce(Avg("reviews__rating"), Value(0.0)),
        reviews_count=Count("reviews", distinct=True),
    )
    if include_tags:
        queryset = queryset.prefetch_related("tags")
    if only_primary:
        queryset = queryset.filter(is_primary_offer=True)
    return queryset if include_inactive else queryset.filter(is_active=True)


def price_similarity_score(first_price, second_price) -> int:
    if not first_price or not second_price:
        return 0
    average_price = (Decimal(first_price) + Decimal(second_price)) / Decimal("2")
    if average_price == 0:
        return 0
    distance = abs(Decimal(first_price) - Decimal(second_price)) / average_price
    if distance <= Decimal("0.15"):
        return 2
    if distance <= Decimal("0.30"):
        return 1
    return 0


def discount_percent(product: Product) -> int:
    if not product.old_price or Decimal(product.old_price) <= Decimal(product.price):
        return 0
    ratio = (Decimal(product.old_price) - Decimal(product.price)) / Decimal(product.old_price)
    return int(round(ratio * 100))


def unique_offer_groups(products, limit: int | None = None):
    unique = []
    seen_groups = set()
    for product in products:
        group_key = product.offer_group or f"id-{product.id}"
        if group_key in seen_groups:
            continue
        seen_groups.add(group_key)
        unique.append(product)
        if limit and len(unique) >= limit:
            break
    return unique
