from django.contrib import admin

from .models import Category, Product, ProductViewHistory, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "seller", "category", "offer_group", "price", "stock", "is_active", "created_at")
    list_filter = ("is_active", "category", "seller")
    search_fields = ("name", "offer_group", "description", "seller__shop_name")
    autocomplete_fields = ("seller", "category", "tags")


@admin.register(ProductViewHistory)
class ProductViewHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "viewed_at")
    search_fields = ("user__username", "product__name")
