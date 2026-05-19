import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from cart.models import Cart, CartItem
from orders.models import Branch, Order, OrderItem
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
        price=Decimal("500.00"),
        stock=10,
        is_active=True,
    )


@pytest.fixture
def cart_with_item(buyer, product):
    cart, _ = Cart.objects.get_or_create(user=buyer)
    CartItem.objects.create(cart=cart, product=product, quantity=2)
    return cart


@pytest.fixture
def authenticated_client(api_client, buyer):
    api_client.force_authenticate(user=buyer)
    return api_client


@pytest.fixture
def seller_client(api_client, seller_user, seller_profile):
    api_client.force_authenticate(user=seller_user)
    return api_client


@pytest.fixture
def branch(db):
    return Branch.objects.create(
        name="Main Branch",
        city="Almaty",
        address="123 Main St",
        latitude=Decimal("43.238949"),
        longitude=Decimal("76.945465"),
        is_active=True,
    )


@pytest.mark.django_db
class TestOrderCreate:
    def test_create_order_from_cart(self, authenticated_client, cart_with_item, product):
        response = authenticated_client.post(
            "/api/orders/create/",
            {"payment_method": "cash_on_delivery"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "processing"
        assert Decimal(response.data["total_amount"]) == Decimal("1000.00")
        assert len(response.data["items"]) == 1
        product.refresh_from_db()
        assert product.stock == 8

    def test_create_order_empty_cart(self, authenticated_client):
        response = authenticated_client.post(
            "/api/orders/create/",
            {"payment_method": "cash_on_delivery"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_order_unauthenticated(self, api_client):
        response = api_client.post(
            "/api/orders/create/",
            {"payment_method": "cash_on_delivery"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_order_with_pickup(self, authenticated_client, cart_with_item, branch):
        response = authenticated_client.post(
            "/api/orders/create/",
            {
                "payment_method": "cash_on_delivery",
                "delivery_method": "pickup",
                "branch_id": branch.id,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["delivery_method"] == "pickup"

    def test_create_order_clears_cart(self, authenticated_client, buyer, cart_with_item):
        authenticated_client.post(
            "/api/orders/create/",
            {"payment_method": "cash_on_delivery"},
            format="json",
        )
        assert CartItem.objects.filter(cart__user=buyer).count() == 0


@pytest.mark.django_db
class TestOrderList:
    def test_list_orders(self, authenticated_client, cart_with_item):
        authenticated_client.post(
            "/api/orders/create/",
            {"payment_method": "cash_on_delivery"},
            format="json",
        )
        response = authenticated_client.get("/api/orders/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_list_orders_unauthenticated(self, api_client):
        response = api_client.get("/api/orders/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestOrderDetail:
    def test_get_order_detail(self, authenticated_client, cart_with_item):
        create_response = authenticated_client.post(
            "/api/orders/create/",
            {"payment_method": "cash_on_delivery"},
            format="json",
        )
        order_id = create_response.data["id"]
        response = authenticated_client.get(f"/api/orders/{order_id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == order_id

    def test_get_other_users_order(self, api_client, buyer):
        other_user = User.objects.create_user(
            username="other", email="other@example.com", password="testpass123",
        )
        order = Order.objects.create(user=buyer, total_amount=Decimal("100.00"))
        api_client.force_authenticate(user=other_user)
        response = api_client.get(f"/api/orders/{order.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestBranchList:
    def test_list_branches(self, api_client, branch):
        response = api_client.get("/api/branches/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Main Branch"


@pytest.mark.django_db
class TestSellerOrders:
    def test_seller_can_see_their_orders(self, buyer, seller_user, seller_profile, cart_with_item):
        buyer_client = APIClient()
        buyer_client.force_authenticate(user=buyer)
        buyer_client.post(
            "/api/orders/create/",
            {"payment_method": "cash_on_delivery"},
            format="json",
        )
        seller_api = APIClient()
        seller_api.force_authenticate(user=seller_user)
        response = seller_api.get("/api/orders/seller/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_non_seller_cannot_access_seller_orders(self, authenticated_client):
        response = authenticated_client.get("/api/orders/seller/")
        assert response.status_code == status.HTTP_403_FORBIDDEN
