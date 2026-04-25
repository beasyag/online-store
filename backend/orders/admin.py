from django.contrib import admin

from .models import Branch, Order, OrderItem


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "address", "working_hours", "is_active")
    list_filter = ("city", "is_active")
    search_fields = ("name", "city", "address")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "seller", "quantity", "price_at_purchase")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "payment_method", "delivery_method", "total_amount", "created_at")
    list_filter = ("status", "payment_method", "delivery_method")
    search_fields = ("user__email",)
    readonly_fields = ("stripe_checkout_session_id", "stripe_payment_intent_id", "total_amount", "created_at", "updated_at")
    inlines = [OrderItemInline]
