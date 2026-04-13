from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import F
from rest_framework import serializers
import stripe

from cart.services import get_or_create_cart
from products.models import Product

from .models import Order, OrderItem


def get_stripe_client():
    if not settings.STRIPE_SECRET_KEY:
        raise serializers.ValidationError({"detail": "Stripe is not configured."})
    return stripe.StripeClient(api_key=settings.STRIPE_SECRET_KEY)


@transaction.atomic
def create_order_from_cart(user, payment_method=Order.PaymentMethod.CARD_ON_DELIVERY):
    cart = get_or_create_cart(user)
    cart_items = list(cart.items.select_related("product__seller").all())
    if not cart_items:
        raise serializers.ValidationError({"detail": "Cart is empty."})

    product_ids = sorted({item.product_id for item in cart_items})
    locked_products = {
        product.id: product
        for product in Product.objects.select_for_update().select_related("seller").filter(id__in=product_ids).order_by("id")
    }

    order = Order.objects.create(
        user=user,
        status=Order.Status.PENDING if payment_method == Order.PaymentMethod.CARD_ONLINE else Order.Status.PROCESSING,
        payment_method=payment_method,
        total_amount=Decimal("0.00"),
    )
    order_items = []
    total_amount = Decimal("0.00")

    for cart_item in cart_items:
        product = locked_products.get(cart_item.product_id)
        if product is None:
            raise serializers.ValidationError({"detail": "One of the products in the cart no longer exists."})
        if not product.is_active:
            raise serializers.ValidationError({"detail": f"{product.name} is not available."})
        if product.stock < cart_item.quantity:
            raise serializers.ValidationError({"detail": f"Not enough stock for {product.name}."})

        order_items.append(
            OrderItem(
                order=order,
                product=product,
                seller=product.seller,
                quantity=cart_item.quantity,
                price_at_purchase=product.price,
            )
        )
        total_amount += Decimal(product.price) * cart_item.quantity
        Product.objects.filter(pk=product.pk).update(
            stock=F("stock") - cart_item.quantity,
            purchases_count=F("purchases_count") + cart_item.quantity,
        )
        product.stock -= cart_item.quantity
        product.purchases_count += cart_item.quantity

    OrderItem.objects.bulk_create(order_items)
    order.total_amount = total_amount
    order.save(update_fields=["total_amount"])
    cart.items.all().delete()

    return order


def create_checkout_session_for_order(order):
    if order.payment_method != Order.PaymentMethod.CARD_ONLINE:
        raise serializers.ValidationError({"detail": "Stripe checkout is available only for online card payments."})
    if order.status in {Order.Status.PAID, Order.Status.COMPLETED}:
        raise serializers.ValidationError({"detail": "Order is already paid."})

    client = get_stripe_client()
    frontend_base_url = settings.FRONTEND_BASE_URL
    line_items = []

    for item in order.items.select_related("product").all():
        product_name = item.product.name if item.product else "Deleted product"
        line_items.append(
            {
                "quantity": item.quantity,
                "price_data": {
                    "currency": "kzt",
                    "unit_amount": int(Decimal(item.price_at_purchase) * 100),
                    "product_data": {
                        "name": product_name,
                    },
                },
            }
        )

    session = client.v1.checkout.sessions.create(
        params={
            "success_url": f"{frontend_base_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": f"{frontend_base_url}/payment/cancel?order_id={order.pk}",
            "mode": "payment",
            "client_reference_id": str(order.pk),
            "customer_email": order.user.email,
            "line_items": line_items,
            "metadata": {"order_id": str(order.pk), "user_id": str(order.user_id)},
        }
    )

    order.stripe_checkout_session_id = session.id
    order.save(update_fields=["stripe_checkout_session_id"])
    return session


@transaction.atomic
def confirm_order_payment(user, session_id):
    client = get_stripe_client()
    session = client.v1.checkout.sessions.retrieve(session_id)

    session_data = getattr(session, "_data", {}) or {}
    metadata = session_data.get("metadata") or {}
    if hasattr(metadata, "_data"):
        metadata = metadata._data or {}
    order_id = metadata.get("order_id")
    if not order_id:
        raise serializers.ValidationError({"detail": "Stripe session is not linked to an order."})

    order = Order.objects.select_for_update().prefetch_related("items__product", "items__seller").get(pk=order_id, user=user)

    if order.payment_method != Order.PaymentMethod.CARD_ONLINE:
        raise serializers.ValidationError({"detail": "Order does not require online payment."})

    if session.payment_status != "paid":
        raise serializers.ValidationError({"detail": "Payment is not completed yet."})

    updated_fields = []
    if order.status != Order.Status.PAID:
        order.status = Order.Status.PAID
        updated_fields.append("status")
    payment_intent = getattr(session, "payment_intent", "") or ""
    if payment_intent and order.stripe_payment_intent_id != payment_intent:
        order.stripe_payment_intent_id = payment_intent
        updated_fields.append("stripe_payment_intent_id")
    if order.stripe_checkout_session_id != session.id:
        order.stripe_checkout_session_id = session.id
        updated_fields.append("stripe_checkout_session_id")
    if updated_fields:
        order.save(update_fields=updated_fields)

    return order
