import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

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
    return SellerProfile.objects.create(
        user=seller_user,
        shop_name="Cool Shop",
        description="Best shop ever",
    )


@pytest.fixture
def authenticated_client(api_client, buyer):
    api_client.force_authenticate(user=buyer)
    return api_client


@pytest.fixture
def seller_client(api_client, seller_user):
    api_client.force_authenticate(user=seller_user)
    return api_client


@pytest.mark.django_db
class TestSellerList:
    def test_list_sellers(self, api_client, seller_profile):
        response = api_client.get("/api/sellers/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["shop_name"] == "Cool Shop"

    def test_list_sellers_empty(self, api_client):
        response = api_client.get("/api/sellers/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0


@pytest.mark.django_db
class TestSellerDetail:
    def test_get_seller_detail(self, api_client, seller_profile):
        response = api_client.get(f"/api/sellers/{seller_profile.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["shop_name"] == "Cool Shop"

    def test_get_nonexistent_seller(self, api_client):
        response = api_client.get("/api/sellers/99999/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCurrentSellerProfile:
    def test_get_own_seller_profile(self, seller_client, seller_profile):
        response = seller_client.get("/api/seller/profile/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["shop_name"] == "Cool Shop"

    def test_buyer_has_no_seller_profile(self, authenticated_client):
        response = authenticated_client.get("/api/seller/profile/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_seller_profile(self, authenticated_client, buyer):
        response = authenticated_client.post(
            "/api/seller/profile/",
            {"shop_name": "Buyer Shop", "description": "My new shop"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        buyer.refresh_from_db()
        assert buyer.role == User.Role.SELLER
        assert buyer.seller_profile.shop_name == "Buyer Shop"

    def test_cannot_create_second_profile(self, seller_client, seller_profile):
        response = seller_client.post(
            "/api/seller/profile/",
            {"shop_name": "Another Shop"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_seller_profile(self, seller_client, seller_profile):
        response = seller_client.patch(
            "/api/seller/profile/",
            {"description": "Updated description"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        seller_profile.refresh_from_db()
        assert seller_profile.description == "Updated description"

    def test_unauthenticated_cannot_access_profile(self, api_client):
        response = api_client.get("/api/seller/profile/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
