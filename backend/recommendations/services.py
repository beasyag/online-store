import math
from collections import Counter
from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone

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

COLLABORATIVE_WEIGHT = 4
TRENDING_WEIGHT = 3

TRENDING_WINDOW_DAYS = 7
TIME_DECAY_HALF_LIFE_DAYS = 14
MAX_CATEGORIES_IN_RESULT = 4


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


# ── Trending ────────────────────────────────────────────────────────

def trending_score(product: Product) -> float:
    """Score based on recent purchase velocity vs. lifetime average."""
    cutoff = timezone.now() - timedelta(days=TRENDING_WINDOW_DAYS)
    recent_purchases = OrderItem.objects.filter(
        product=product,
        order__created_at__gte=cutoff,
    ).count()
    if recent_purchases == 0:
        return 0.0
    lifetime_avg_per_week = product.purchases_count / max((timezone.now() - product.created_at).days / 7, 1)
    if lifetime_avg_per_week <= 0:
        ratio = 1.0
    else:
        ratio = recent_purchases / lifetime_avg_per_week
    return round(min(ratio, 3.0) / 3.0, 2)


def get_trending_products(limit: int = 12):
    cutoff = timezone.now() - timedelta(days=TRENDING_WINDOW_DAYS)
    recent_ids = (
        OrderItem.objects
        .filter(order__created_at__gte=cutoff)
        .values("product_id")
        .annotate(cnt=Count("id"))
        .order_by("-cnt")
        .values_list("product_id", flat=True)[:limit * 3]
    )
    candidates = list(
        get_product_queryset(only_primary=True)
        .filter(id__in=list(recent_ids))
    )
    for candidate in candidates:
        candidate.recommendation_score = round(
            trending_score(candidate) * TRENDING_WEIGHT + popularity_bonus(candidate), 2,
        )
    candidates.sort(
        key=lambda p: (p.recommendation_score, p.purchases_count),
        reverse=True,
    )
    return candidates[:limit]


# ── Collaborative filtering ────────────────────────────────────────

def _co_purchased_product_ids(product_ids: set[int], exclude_ids: set[int], limit: int = 60) -> list[int]:
    """Find products frequently bought by the same users who bought *product_ids*."""
    if not product_ids:
        return []
    buyer_ids = list(
        OrderItem.objects
        .filter(product_id__in=product_ids)
        .values_list("order__user_id", flat=True)
        .distinct()[:200]
    )
    if not buyer_ids:
        return []
    co_bought = (
        OrderItem.objects
        .filter(order__user_id__in=buyer_ids)
        .exclude(product_id__in=product_ids | exclude_ids)
        .values("product_id")
        .annotate(cnt=Count("id"))
        .order_by("-cnt")
        .values_list("product_id", flat=True)[:limit]
    )
    return list(co_bought)


def get_also_bought_products(product: Product, limit: int = 8):
    """'С этим товаром покупают' for a product detail page."""
    co_ids = _co_purchased_product_ids({product.id}, {product.id}, limit=limit * 3)
    if not co_ids:
        return get_similar_products(product, limit=limit)

    candidates = list(get_product_queryset(only_primary=True).filter(id__in=co_ids))
    co_rank = {pid: idx for idx, pid in enumerate(co_ids)}
    for candidate in candidates:
        rank_bonus = max(0, 1 - co_rank.get(candidate.id, len(co_ids)) / max(len(co_ids), 1))
        candidate.recommendation_score = round(rank_bonus * COLLABORATIVE_WEIGHT + popularity_bonus(candidate), 2)
    candidates.sort(
        key=lambda p: (p.recommendation_score, p.purchases_count),
        reverse=True,
    )
    return candidates[:limit]


# ── Time-decay helpers ──────────────────────────────────────────────

def _time_decay_factor(days_ago: float) -> float:
    """Exponential decay: weight halves every TIME_DECAY_HALF_LIFE_DAYS."""
    return math.pow(0.5, days_ago / TIME_DECAY_HALF_LIFE_DAYS)


def _get_user_signal_product_ids_with_recency(user) -> dict[str, list[tuple[int, float]]]:
    """Return product_id → recency_weight pairs per signal type."""
    if not getattr(user, "is_authenticated", False):
        return {"viewed": [], "favorite": [], "cart": [], "purchased": []}

    now = timezone.now()

    viewed_qs = (
        ProductViewHistory.objects
        .filter(user=user)
        .order_by("-viewed_at")
        .values_list("product_id", "viewed_at")[:40]
    )
    viewed = [(pid, _time_decay_factor((now - ts).total_seconds() / 86400)) for pid, ts in viewed_qs]

    fav_qs = Favorite.objects.filter(user=user).values_list("product_id", "created_at")[:40]
    favorites = [(pid, _time_decay_factor((now - ts).total_seconds() / 86400)) for pid, ts in fav_qs]

    cart_items = list(CartItem.objects.filter(cart__user=user).values_list("product_id", flat=True)[:40])
    cart = [(pid, 1.0) for pid in cart_items]

    purchased_qs = (
        OrderItem.objects
        .filter(order__user=user)
        .values_list("product_id", "order__created_at")[:40]
    )
    purchased = [(pid, _time_decay_factor((now - ts).total_seconds() / 86400)) for pid, ts in purchased_qs]

    return {
        "viewed": viewed,
        "favorite": favorites,
        "cart": cart,
        "purchased": purchased,
    }


# ── Diversity enforcement ──────────────────────────────────────────

def _enforce_diversity(scored_products: list[Product], limit: int) -> list[Product]:
    """Pick top products while capping per-category and per-seller representation."""
    result: list[Product] = []
    seen_groups: set[str] = set()
    category_counts: Counter[int] = Counter()
    seller_counts: Counter[int] = Counter()

    max_per_category = max(3, limit // MAX_CATEGORIES_IN_RESULT)
    max_per_seller = max(2, limit // 4)

    for product in scored_products:
        group_key = product.offer_group or f"id-{product.id}"
        if group_key in seen_groups:
            continue
        if category_counts[product.category_id] >= max_per_category:
            continue
        if seller_counts[product.seller_id] >= max_per_seller:
            continue
        seen_groups.add(group_key)
        category_counts[product.category_id] += 1
        seller_counts[product.seller_id] += 1
        result.append(product)
        if len(result) >= limit:
            break

    if len(result) < limit:
        for product in scored_products:
            group_key = product.offer_group or f"id-{product.id}"
            if group_key in seen_groups:
                continue
            seen_groups.add(group_key)
            result.append(product)
            if len(result) >= limit:
                break

    return result


# ── Public list helpers ─────────────────────────────────────────────

def get_popular_products(limit: int = 12):
    return list(get_product_queryset(only_primary=True).order_by("-purchases_count", "-views_count", "-average_rating")[:limit])


def get_new_products(limit: int = 12):
    return list(get_product_queryset(only_primary=True).order_by("-created_at")[:limit])


def get_similar_products(product: Product, limit: int = 8):
    tag_ids = {tag.id for tag in product.tags.all()}
    candidates_qs = get_product_queryset(only_primary=True).exclude(pk=product.pk)

    if product.offer_group:
        candidates_qs = candidates_qs.exclude(offer_group=product.offer_group)

    filters = Q(category_id=product.category_id)
    if tag_ids:
        filters |= Q(tags__id__in=tag_ids)
    candidates_qs = candidates_qs.filter(filters).distinct()

    candidates_qs = candidates_qs.order_by(
        "-purchases_count", "-views_count", "-created_at",
    )[:limit * 10]

    candidates = list(candidates_qs)
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


# ── Internal helpers for personalized recommendations ───────────────

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


def _signal_score_with_decay(
    candidate: Product,
    references: list[Product],
    recency_map: dict[int, float],
    weight: int,
) -> float:
    """Like _signal_score but multiplies each reference similarity by its recency weight."""
    if not references:
        return 0.0
    best = 0.0
    for ref in references:
        sim = base_similarity_score(candidate, ref)
        if sim > 0:
            decay = recency_map.get(ref.id, 1.0)
            best = max(best, sim * decay)
    if best <= 0:
        return 0.0
    return round((best / MAX_BASE_SCORE) * weight, 2)


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


# ── Main recommendation entry point ────────────────────────────────

def get_recommendations_for_user(user, limit: int = 12):
    if not getattr(user, "is_authenticated", False):
        return get_popular_products(limit=limit), "popular_fallback"

    signal_ids = _get_user_signal_product_ids(user)
    purchased_ids = signal_ids["purchased"]

    signal_recency = _get_user_signal_product_ids_with_recency(user)
    recency_maps: dict[str, dict[int, float]] = {}
    for signal_name, pairs in signal_recency.items():
        recency_maps[signal_name] = {pid: w for pid, w in pairs}

    signal_products = {
        signal_name: _fetch_reference_products(product_ids) for signal_name, product_ids in signal_ids.items()
    }

    has_any_signal = any(signal_products.values())
    if not has_any_signal:
        return get_popular_products(limit=limit), "popular_fallback"

    co_purchased_ids = _co_purchased_product_ids(purchased_ids | signal_ids["cart"], purchased_ids)
    co_purchased_set = set(co_purchased_ids)
    co_rank = {pid: idx for idx, pid in enumerate(co_purchased_ids)}

    candidates_qs = _candidate_queryset_for_signals(signal_products, purchased_ids)
    extra_qs = get_product_queryset(only_primary=True).filter(id__in=co_purchased_ids).exclude(id__in=purchased_ids)

    candidate_map: dict[int, Product] = {}
    for p in candidates_qs:
        candidate_map[p.id] = p
    for p in extra_qs:
        if p.id not in candidate_map:
            candidate_map[p.id] = p

    scored_products = []
    for candidate in candidate_map.values():
        score = popularity_bonus(candidate)

        for signal_name, references in signal_products.items():
            score += _signal_score_with_decay(
                candidate, references, recency_maps[signal_name], USER_SIGNAL_WEIGHTS[signal_name],
            )

        if candidate.id in co_purchased_set:
            rank_bonus = max(0, 1 - co_rank.get(candidate.id, len(co_purchased_ids)) / max(len(co_purchased_ids), 1))
            score += rank_bonus * COLLABORATIVE_WEIGHT

        ts = trending_score(candidate)
        if ts > 0:
            score += ts * TRENDING_WEIGHT

        if score > 0:
            candidate.recommendation_score = round(score, 2)
            scored_products.append(candidate)

    scored_products.sort(
        key=lambda item: (item.recommendation_score, item.purchases_count, item.views_count, item.created_at),
        reverse=True,
    )

    return _enforce_diversity(scored_products, limit), "personalized"
