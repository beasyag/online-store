"""Offline evaluation of the recommendation engine.

Produces reproducible quality metrics for the personalized scoring model and
compares them with a ``popular`` baseline, so the figures quoted in reports come
from the actual seeded data instead of a static number.

Protocol (leave-one-out)
------------------------
For every buyer with at least ``--min-purchases`` purchased products:

1. One purchased product is held out as the ground-truth item to predict.
2. Inside a transaction that is rolled back afterwards, the held-out purchase is
   removed so the engine neither uses it as a signal nor filters it out as
   "already bought". This lets the exact production code path
   (``get_recommendations_for_user``) run against a realistic train/test split.
3. The held-out item (matched by ``offer_group`` so multi-vendor duplicates
   count) is "relevant". We measure whether it appears in the Top-K list.

Reported metrics (averaged over evaluated users):
* HitRate@K  - share of users whose held-out purchase appears in Top-K.
* Precision@K - relevant items in Top-K divided by K.

Usage:
    python manage.py evaluate_recommendations
    python manage.py evaluate_recommendations --k 10 --min-purchases 2 --seed 42
"""

from __future__ import annotations

import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from orders.models import OrderItem
from recommendations.services import get_popular_products, get_recommendations_for_user

User = get_user_model()


def _group_key(product) -> str:
    return product.offer_group or f"id-{product.id}"


class _Rollback(Exception):
    """Raised to roll back the temporary train/test split without committing."""


class Command(BaseCommand):
    help = "Leave-one-out evaluation of HitRate@K / Precision@K vs a popular baseline."

    def add_arguments(self, parser):
        parser.add_argument("--k", type=int, default=10, help="Cut-off K.")
        parser.add_argument(
            "--min-purchases",
            type=int,
            default=2,
            help="Only evaluate users with at least this many purchased products.",
        )
        parser.add_argument(
            "--limit-users",
            type=int,
            default=0,
            help="Optional cap on the number of evaluated users (0 = no cap).",
        )
        parser.add_argument("--seed", type=int, default=42, help="RNG seed for the held-out split.")

    def _purchased_items(self, user):
        return list(
            OrderItem.objects.filter(order__user=user, product__isnull=False).select_related("product")
        )

    def _evaluate_user(self, user, k: int, rng: random.Random):
        items = self._purchased_items(user)
        if len({item.product_id for item in items}) < self.min_purchases:
            return None

        held_out_item = rng.choice(items)
        held_out_group = _group_key(held_out_item.product)
        held_out_order_item_ids = [
            item.id for item in items if _group_key(item.product) == held_out_group
        ]

        captured: dict = {}
        try:
            with transaction.atomic():
                OrderItem.objects.filter(id__in=held_out_order_item_ids).delete()
                captured["recs"], captured["strategy"] = get_recommendations_for_user(user, limit=k)
                raise _Rollback
        except _Rollback:
            pass

        personalized = captured["recs"]
        if captured["strategy"] != "personalized":
            return None

        baseline = get_popular_products(limit=k)
        return {
            "personalized_hit": any(_group_key(p) == held_out_group for p in personalized[:k]),
            "baseline_hit": any(_group_key(p) == held_out_group for p in baseline[:k]),
            "personalized_precision": sum(_group_key(p) == held_out_group for p in personalized[:k]) / k,
            "baseline_precision": sum(_group_key(p) == held_out_group for p in baseline[:k]) / k,
        }

    def handle(self, *args, **options):
        k = options["k"]
        self.min_purchases = options["min_purchases"]
        limit_users = options["limit_users"]
        rng = random.Random(options["seed"])

        buyer_ids = list(
            OrderItem.objects.filter(product__isnull=False)
            .values_list("order__user_id", flat=True)
            .distinct()
        )

        totals = {
            "personalized_hit": 0,
            "baseline_hit": 0,
            "personalized_precision": 0.0,
            "baseline_precision": 0.0,
        }
        evaluated = 0

        for user in User.objects.filter(id__in=buyer_ids).iterator():
            result = self._evaluate_user(user, k, rng)
            if result is None:
                continue
            for key in totals:
                totals[key] += result[key]
            evaluated += 1
            if limit_users and evaluated >= limit_users:
                break

        if not evaluated:
            self.stdout.write(self.style.WARNING("No users with usable signals were found. Seed data first."))
            return

        hit_p = totals["personalized_hit"] / evaluated
        hit_b = totals["baseline_hit"] / evaluated
        prec_p = totals["personalized_precision"] / evaluated
        prec_b = totals["baseline_precision"] / evaluated
        uplift = (hit_p / hit_b) if hit_b else float("inf")

        self.stdout.write(self.style.SUCCESS(f"Evaluated users: {evaluated}"))
        self.stdout.write(f"HitRate@{k}  personalized: {hit_p:.3f} | baseline: {hit_b:.3f} | uplift x{uplift:.2f}")
        self.stdout.write(f"Precision@{k} personalized: {prec_p:.3f} | baseline: {prec_b:.3f}")
