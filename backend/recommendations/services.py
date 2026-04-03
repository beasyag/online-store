from django.db.models import Q

from cart.models import CartItem
from favorites.models import Favorite
from orders.models import OrderItem
from products.models import Product, ProductViewHistory
from products.services import get_product_queryset, price_similarity_score

BASE_CATEGORY_SCORE = 3
BASE_TAG_SCORE = 2
MAX_BASE_SCORE = 7

USER_SIGNAL_WEIGHTS = {
    "viewed": 4,
    "purchased": 5,
    "favorite": 3,
    "cart": 3,
}


def _tag_ids(product) -> set[int]:
    if not hasattr(product, "_cached_tag_ids"):
        product._cached_tag_ids = {tag.id for tag in product.tags.all()}
    return product._cached_tag_ids


def base_similarity_score(candidate: Product, reference: Product) -> int:
    if candidate.id == reference.id:
        return 0
    if candidate.offer_group and reference.offer_group and candidate.offer_group == reference.offer_group:
        return 0

    score = 0
    if candidate.category_id == reference.category_id:
        score += BASE_CATEGORY_SCORE

    score += price_similarity_score(candidate.price, reference.price)

    shared_tags = _tag_ids(candidate).intersection(_tag_ids(reference))
    if shared_tags:
        score += min(BASE_TAG_SCORE, len(shared_tags))

    return score


def popularity_bonus(product: Product) -> float:
    views_component = min(product.views_count / 500, 1)
    purchases_component = min(product.purchases_count / 100, 1)
    rating_component = min(float(getattr(product, "average_rating", 0) or 0) / 5, 1)
    return round(((views_component * 0.35) + (purchases_component * 0.45) + (rating_component * 0.20)) * 2, 2)


def get_popular_products(limit: int = 12):
    return list(get_product_queryset(only_primary=True).order_by("-purchases_count", "-views_count", "-average_rating")[:limit])


def get_new_products(limit: int = 12):
    return list(get_product_queryset(only_primary=True).order_by("-created_at")[:limit])


def get_similar_products(product: Product, limit: int = 8):
    candidates = list(get_product_queryset(only_primary=True).exclude(pk=product.pk))
    scored_products = []
    for candidate in candidates:
        score = base_similarity_score(candidate, product) + popularity_bonus(candidate)
        if score > 0:
            candidate.recommendation_score = round(score, 2)
            scored_products.append(candidate)

    scored_products.sort(
        key=lambda item: (item.recommendation_score, item.purchases_count, item.views_count, item.created_at),
        reverse=True,
    )
    return scored_products[:limit]


def _fetch_reference_products(product_ids: set[int]):
    if not product_ids:
        return []
    reference_map = {product.id: product for product in get_product_queryset(include_inactive=True).filter(id__in=product_ids)}
    return [reference_map[product_id] for product_id in product_ids if product_id in reference_map]


def _get_user_signal_product_ids(user) -> dict[str, set[int]]:
    if not getattr(user, "is_authenticated", False):
        return {"viewed": set(), "favorite": set(), "cart": set(), "purchased": set()}

    return {
        "viewed": set(
            ProductViewHistory.objects.filter(user=user).order_by("-viewed_at").values_list("product_id", flat=True)[:40]
        ),
        "favorite": set(Favorite.objects.filter(user=user).values_list("product_id", flat=True)[:40]),
        "cart": set(CartItem.objects.filter(cart__user=user).values_list("product_id", flat=True)[:40]),
        "purchased": set(OrderItem.objects.filter(order__user=user).values_list("product_id", flat=True)[:40]),
    }


def _signal_score(candidate: Product, references: list[Product], weight: int) -> float:
    if not references:
        return 0.0
    highest_similarity = max(base_similarity_score(candidate, reference) for reference in references)
    if highest_similarity <= 0:
        return 0.0
    return round((highest_similarity / MAX_BASE_SCORE) * weight, 2)


def _candidate_queryset_for_signals(signal_products: dict[str, list[Product]], purchased_ids: set[int]):
    category_ids = {product.category_id for products in signal_products.values() for product in products if product.category_id}
    tag_ids = {tag.id for products in signal_products.values() for product in products for tag in product.tags.all()}

    queryset = get_product_queryset(only_primary=True).exclude(id__in=purchased_ids)
    if category_ids or tag_ids:
        filters = Q()
        if category_ids:
            filters |= Q(category_id__in=category_ids)
        if tag_ids:
            filters |= Q(tags__id__in=tag_ids)
        queryset = queryset.filter(filters)

    return queryset.order_by("-purchases_count", "-views_count", "-average_rating", "-created_at").distinct()[:250]


def get_recommendations_for_user(user, limit: int = 12):
    if not getattr(user, "is_authenticated", False):
        return get_popular_products(limit=limit), "popular_fallback"

    signal_ids = _get_user_signal_product_ids(user)
    purchased_ids = signal_ids["purchased"]

    signal_products = {
        signal_name: _fetch_reference_products(product_ids) for signal_name, product_ids in signal_ids.items()
    }

    has_any_signal = any(signal_products.values())
    if not has_any_signal:
        return get_popular_products(limit=limit), "popular_fallback"

    candidates = list(_candidate_queryset_for_signals(signal_products, purchased_ids))
    scored_products = []

    for candidate in candidates:
        score = popularity_bonus(candidate)
        for signal_name, references in signal_products.items():
            score += _signal_score(candidate, references, USER_SIGNAL_WEIGHTS[signal_name])
        if score > 0:
            candidate.recommendation_score = round(score, 2)
            scored_products.append(candidate)

    scored_products.sort(
        key=lambda item: (item.recommendation_score, item.purchases_count, item.views_count, item.created_at),
        reverse=True,
    )
    unique_products = []
    seen_groups = set()
    for product in scored_products:
        group_key = product.offer_group or f"id-{product.id}"
        if group_key in seen_groups:
            continue
        seen_groups.add(group_key)
        unique_products.append(product)
        if len(unique_products) >= limit:
            break
    return unique_products, "personalized"
