import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from products.models import Category, Product, Tag
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
def category2(db):
    return Category.objects.create(name="Books", slug="books")


@pytest.fixture
def tag(db):
    return Tag.objects.create(name="Sale", slug="sale")


@pytest.fixture
def product(seller_profile, category, tag):
    p = Product.objects.create(
        seller=seller_profile,
        name="Smartphone",
        slug="smartphone",
        category=category,
        price=Decimal("500.00"),
        stock=10,
        is_active=True,
    )
    p.tags.add(tag)
    return p


@pytest.fixture
def product2(seller_profile, category2):
    return Product.objects.create(
        seller=seller_profile,
        name="Novel",
        slug="novel",
        category=category2,
        price=Decimal("20.00"),
        stock=50,
        is_active=True,
    )


@pytest.fixture
def inactive_product(seller_profile, category):
    return Product.objects.create(
        seller=seller_profile,
        name="Old Phone",
        slug="old-phone",
        category=category,
        price=Decimal("50.00"),
        stock=0,
        is_active=False,
    )


@pytest.fixture
def authenticated_client(api_client, buyer):
    api_client.force_authenticate(user=buyer)
    return api_client


@pytest.fixture
def seller_client(api_client, seller_user, seller_profile):
    api_client.force_authenticate(user=seller_user)
    return api_client


@pytest.mark.django_db
class TestCategoryList:
    def test_list_categories(self, api_client, category, category2):
        response = api_client.get("/api/categories/")
        assert response.status_code == status.HTTP_200_OK
        slugs = [c["slug"] for c in response.data["results"]]
        assert "electronics" in slugs
        assert "books" in slugs


@pytest.mark.django_db
class TestTagList:
    def test_list_tags(self, api_client, tag):
        response = api_client.get("/api/tags/")
        assert response.status_code == status.HTTP_200_OK
        names = [t["name"] for t in response.data["results"]]
        assert "Sale" in names


@pytest.mark.django_db
class TestProductList:
    def test_list_products(self, api_client, product, product2):
        response = api_client.get("/api/products/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_list_excludes_inactive(self, api_client, product, inactive_product):
        response = api_client.get("/api/products/")
        slugs = [p["slug"] for p in response.data["results"]]
        assert "old-phone" not in slugs

    def test_filter_by_category(self, api_client, product, product2):
        response = api_client.get(f"/api/products/?category={product.category_id}")
        for p in response.data["results"]:
            assert p["category"]["id"] == product.category_id


@pytest.mark.django_db
class TestProductDetail:
    def test_get_product_detail(self, api_client, product):
        response = api_client.get(f"/api/products/{product.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Smartphone"

    def test_get_nonexistent_product(self, api_client):
        response = api_client.get("/api/products/99999/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestProductCreate:
    def test_seller_can_create_product(self, seller_client, category, tag):
        data = {
            "category_id": category.id,
            "name": "New Gadget",
            "description": "A brand new gadget",
            "price": "299.99",
            "stock": 25,
            "tag_ids": [tag.id],
        }
        response = seller_client.post("/api/products/", data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Product.objects.filter(name="New Gadget").exists()

    def test_buyer_cannot_create_product(self, authenticated_client, category):
        data = {
            "category_id": category.id,
            "name": "Fake Product",
            "description": "Should not be created",
            "price": "100.00",
            "stock": 5,
        }
        response = authenticated_client.post("/api/products/", data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_cannot_create_product(self, api_client, category):
        data = {
            "category_id": category.id,
            "name": "No Auth Product",
            "description": "Should fail",
            "price": "50.00",
            "stock": 1,
        }
        response = api_client.post("/api/products/", data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestProductPopular:
    def test_popular_products(self, api_client, product, product2):
        product.purchases_count = 100
        product.save(update_fields=["purchases_count"])
        response = api_client.get("/api/products/popular/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0


@pytest.mark.django_db
class TestProductNew:
    def test_new_products(self, api_client, product):
        response = api_client.get("/api/products/new/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0
