from decimal import Decimal

from django.db import transaction
from django.db.models import F
from rest_framework import serializers

from cart.services import get_or_create_cart
from products.models import Product

from .models import Order, OrderItem


@transaction.atomic
def create_order_from_cart(user):
    cart = get_or_create_cart(user)
    cart_items = list(cart.items.select_related("product__seller").all())
    if not cart_items:
        raise serializers.ValidationError({"detail": "Cart is empty."})

    product_ids = sorted({item.product_id for item in cart_items})
    locked_products = {
        product.id: product
        for product in Product.objects.select_for_update().select_related("seller").filter(id__in=product_ids).order_by("id")
    }

    order = Order.objects.create(user=user, status=Order.Status.PENDING, total_amount=Decimal("0.00"))
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
    order.status = Order.Status.PROCESSING
    order.save(update_fields=["total_amount", "status"])
    cart.items.all().delete()

    return order
