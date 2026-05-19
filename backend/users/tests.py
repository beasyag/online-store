import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

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
def authenticated_client(api_client, buyer):
    api_client.force_authenticate(user=buyer)
    return api_client


@pytest.mark.django_db
class TestRegister:
    def test_register_buyer(self, api_client):
        data = {
            "username": "newbuyer",
            "email": "newbuyer@example.com",
            "password": "securepass1",
            "role": "buyer",
        }
        response = api_client.post("/api/auth/register/", data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["username"] == "newbuyer"
        assert response.data["role"] == "buyer"
        assert User.objects.filter(username="newbuyer").exists()

    def test_register_seller_requires_shop_name(self, api_client):
        data = {
            "username": "newseller",
            "email": "newseller@example.com",
            "password": "securepass1",
            "role": "seller",
        }
        response = api_client.post("/api/auth/register/", data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_seller_with_shop_name(self, api_client):
        data = {
            "username": "newseller",
            "email": "newseller@example.com",
            "password": "securepass1",
            "role": "seller",
            "shop_name": "My Shop",
        }
        response = api_client.post("/api/auth/register/", data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["role"] == "seller"
        user = User.objects.get(username="newseller")
        assert hasattr(user, "seller_profile")
        assert user.seller_profile.shop_name == "My Shop"

    def test_register_duplicate_username(self, api_client, buyer):
        data = {
            "username": "buyer",
            "email": "other@example.com",
            "password": "securepass1",
            "role": "buyer",
        }
        response = api_client.post("/api/auth/register/", data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_short_password(self, api_client):
        data = {
            "username": "shortpw",
            "email": "short@example.com",
            "password": "abc",
            "role": "buyer",
        }
        response = api_client.post("/api/auth/register/", data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLogin:
    def test_login_success(self, api_client, buyer):
        response = api_client.post(
            "/api/auth/login/",
            {"username": "buyer", "password": "testpass123"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert response.data["user"]["username"] == "buyer"

    def test_login_wrong_password(self, api_client, buyer):
        response = api_client.post(
            "/api/auth/login/",
            {"username": "buyer", "password": "wrongpassword"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, api_client):
        response = api_client.post(
            "/api/auth/login/",
            {"username": "ghost", "password": "testpass123"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestTokenRefresh:
    def test_refresh_success(self, api_client, buyer):
        login = api_client.post(
            "/api/auth/login/",
            {"username": "buyer", "password": "testpass123"},
            format="json",
        )
        refresh_token = login.data["refresh"]
        response = api_client.post(
            "/api/auth/refresh/",
            {"refresh": refresh_token},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_refresh_invalid_token(self, api_client):
        response = api_client.post(
            "/api/auth/refresh/",
            {"refresh": "invalid-token"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestProfile:
    def test_profile_authenticated(self, authenticated_client, buyer):
        response = authenticated_client.get("/api/auth/profile/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == "buyer"
        assert response.data["email"] == "buyer@example.com"

    def test_profile_unauthenticated(self, api_client):
        response = api_client.get("/api/auth/profile/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
