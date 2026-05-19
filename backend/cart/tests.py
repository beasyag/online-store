import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from cart.models import Cart, CartItem
from products.models import Category, Product
from sellers.models import SellerProfile

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def buyer(db):
    return User.objects.create_user(
        username="buyer",
        email="buyer@example.com",
        password="testpass123",
        role=User.Role.BUYER,
    )


@pytest.fixture
def seller_user(db):
    return User.objects.create_user(
        username="seller",
        email="seller@example.com",
        password="testpass123",
        role=User.Role.SELLER,
    )


@pytest.fixture
def seller_profile(seller_user):
    return SellerProfile.objects.create(user=seller_user, shop_name="Test Shop")


@pytest.fixture
def category(db):
    return Category.objects.create(name="Electronics", slug="electronics")


@pytest.fixture
def product(seller_profile, category):
    return Product.objects.create(
        seller=seller_profile,
        name="Test Product",
        slug="test-product",
        category=category,
        price=Decimal("100.00"),
        stock=10,
        is_active=True,
    )


@pytest.fixture
def product2(seller_profile, category):
    return Product.objects.create(
        seller=seller_profile,
        name="Other Product",
        slug="other-product",
        category=category,
        price=Decimal("200.00"),
        stock=5,
        is_active=True,
    )


@pytest.fixture
def authenticated_client(api_client, buyer):
    api_client.force_authenticate(user=buyer)
    return api_client


@pytest.mark.django_db
class TestCartView:
    def test_get_empty_cart(self, authenticated_client):
        response = authenticated_client.get("/api/cart/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_items"] == 0
        assert response.data["items"] == []

    def test_get_cart_unauthenticated(self, api_client):
        response = api_client.get("/api/cart/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestCartAdd:
    def test_add_to_cart(self, authenticated_client, product):
        response = authenticated_client.post(
            "/api/cart/add/",
            {"product_id": product.id, "quantity": 2},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["total_items"] == 2
        assert len(response.data["items"]) == 1

    def test_add_to_cart_exceeds_stock(self, authenticated_client, product):
        response = authenticated_client.post(
            "/api/cart/add/",
            {"product_id": product.id, "quantity": 99},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_add_to_cart_increments_quantity(self, authenticated_client, product):
        authenticated_client.post(
            "/api/cart/add/",
            {"product_id": product.id, "quantity": 2},
            format="json",
        )
        response = authenticated_client.post(
            "/api/cart/add/",
            {"product_id": product.id, "quantity": 3},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["total_items"] == 5

    def test_add_nonexistent_product(self, authenticated_client):
        response = authenticated_client.post(
            "/api/cart/add/",
            {"product_id": 99999, "quantity": 1},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCartItemUpdate:
    def test_update_cart_item(self, authenticated_client, buyer, product):
        authenticated_client.post(
            "/api/cart/add/",
            {"product_id": product.id, "quantity": 2},
            format="json",
        )
        cart = Cart.objects.get(user=buyer)
        item = cart.items.first()
        response = authenticated_client.patch(
            f"/api/cart/item/{item.id}/",
            {"quantity": 5},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_items"] == 5

    def test_update_cart_item_exceeds_stock(self, authenticated_client, buyer, product):
        authenticated_client.post(
            "/api/cart/add/",
            {"product_id": product.id, "quantity": 1},
            format="json",
        )
        cart = Cart.objects.get(user=buyer)
        item = cart.items.first()
        response = authenticated_client.patch(
            f"/api/cart/item/{item.id}/",
            {"quantity": 99},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_cart_item(self, authenticated_client, buyer, product):
        authenticated_client.post(
            "/api/cart/add/",
            {"product_id": product.id, "quantity": 1},
            format="json",
        )
        cart = Cart.objects.get(user=buyer)
        item = cart.items.first()
        response = authenticated_client.delete(f"/api/cart/item/{item.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_items"] == 0
        assert CartItem.objects.filter(cart=cart).count() == 0
