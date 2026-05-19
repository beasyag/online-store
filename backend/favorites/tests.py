import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from favorites.models import Favorite
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
class TestFavoriteToggle:
    def test_add_favorite(self, authenticated_client, product):
        response = authenticated_client.post(
            "/api/favorites/toggle/",
            {"product_id": product.id},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "added"
        assert Favorite.objects.filter(product=product).exists()

    def test_remove_favorite(self, authenticated_client, buyer, product):
        Favorite.objects.create(user=buyer, product=product)
        response = authenticated_client.post(
            "/api/favorites/toggle/",
            {"product_id": product.id},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "removed"
        assert not Favorite.objects.filter(product=product).exists()

    def test_toggle_unauthenticated(self, api_client, product):
        response = api_client.post(
            "/api/favorites/toggle/",
            {"product_id": product.id},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_toggle_nonexistent_product(self, authenticated_client):
        response = authenticated_client.post(
            "/api/favorites/toggle/",
            {"product_id": 99999},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestFavoriteList:
    def test_list_favorites(self, authenticated_client, buyer, product, product2):
        Favorite.objects.create(user=buyer, product=product)
        Favorite.objects.create(user=buyer, product=product2)
        response = authenticated_client.get("/api/favorites/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_list_favorites_empty(self, authenticated_client):
        response = authenticated_client.get("/api/favorites/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

    def test_list_favorites_unauthenticated(self, api_client):
        response = api_client.get("/api/favorites/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
