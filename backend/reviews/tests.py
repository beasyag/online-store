import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from products.models import Category, Product
from reviews.models import Review
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
def buyer2(db):
    return User.objects.create_user(
        username="buyer2",
        email="buyer2@example.com",
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
def authenticated_client(api_client, buyer):
    api_client.force_authenticate(user=buyer)
    return api_client


@pytest.mark.django_db
class TestReviewCreate:
    def test_create_review(self, authenticated_client, product):
        response = authenticated_client.post(
            f"/api/products/{product.id}/reviews/",
            {"rating": 5, "text": "Great product!"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Review.objects.filter(product=product, rating=5).exists()

    def test_cannot_review_twice(self, authenticated_client, product):
        authenticated_client.post(
            f"/api/products/{product.id}/reviews/",
            {"rating": 5, "text": "First review"},
            format="json",
        )
        response = authenticated_client.post(
            f"/api/products/{product.id}/reviews/",
            {"rating": 3, "text": "Second review"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthenticated_cannot_review(self, api_client, product):
        response = api_client.post(
            f"/api/products/{product.id}/reviews/",
            {"rating": 4, "text": "Nice"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_review_invalid_rating(self, authenticated_client, product):
        response = authenticated_client.post(
            f"/api/products/{product.id}/reviews/",
            {"rating": 6, "text": "Too high rating"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestReviewList:
    def test_list_reviews(self, api_client, buyer, buyer2, product):
        Review.objects.create(user=buyer, product=product, rating=5, text="Excellent!")
        Review.objects.create(user=buyer2, product=product, rating=3, text="Average")
        response = api_client.get(f"/api/products/{product.id}/reviews/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def test_list_reviews_empty(self, api_client, product):
        response = api_client.get(f"/api/products/{product.id}/reviews/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0
