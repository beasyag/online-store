import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from products.models import Product, Category, Tag, ProductViewHistory
from sellers.models import SellerProfile
from recommendations.services import (
    base_similarity_score,
    popularity_bonus,
    get_popular_products,
    get_similar_products,
    get_recommendations_for_user,
)

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="testpassword")


@pytest.fixture
def seller(db, user):
    return SellerProfile.objects.create(user=user, shop_name="Test Shop")


@pytest.fixture
def category(db):
    return Category.objects.create(name="Electronics", slug="electronics")


@pytest.fixture
def category2(db):
    return Category.objects.create(name="Books", slug="books")


@pytest.fixture
def tag1(db):
    return Tag.objects.create(name="Sale")


@pytest.fixture
def tag2(db):
    return Tag.objects.create(name="New")


@pytest.fixture
def product1(db, seller, category, tag1):
    p = Product.objects.create(
        seller=seller,
        name="Smartphone X",
        slug="smartphone-x",
        category=category,
        price=Decimal("100.00"),
        is_active=True,
    )
    p.tags.add(tag1)
    return p


@pytest.fixture
def product2(db, seller, category, tag1, tag2):
    p = Product.objects.create(
        seller=seller,
        name="Smartphone Y",
        slug="smartphone-y",
        category=category,
        price=Decimal("105.00"),
        is_active=True,
    )
    p.tags.add(tag1, tag2)
    return p


@pytest.fixture
def product3(db, seller, category2):
    return Product.objects.create(
        seller=seller,
        name="Novel",
        slug="novel",
        category=category2,
        price=Decimal("50.00"),
        is_active=True,
    )


@pytest.mark.django_db
class TestRecommendationAlgorithms:
    def test_base_similarity_score(self, product1, product2, product3):
        score = base_similarity_score(product1, product2)
        assert score > 0, "Products in the same category with shared tags should have a positive score"

        score_diff = base_similarity_score(product1, product3)
        assert score_diff < score, "Products in different categories should score lower"

    def test_popularity_bonus(self, product1):
        product1.views_count = 500
        product1.purchases_count = 100
        product1.average_rating = 5.0
        product1.save()

        bonus = popularity_bonus(product1)
        assert bonus == 2.0, "Max popularity should return bonus 2.0"

    def test_get_popular_products(self, product1, product2):
        product1.purchases_count = 10
        product1.save()
        product2.purchases_count = 5
        product2.save()

        popular = get_popular_products(limit=2)
        assert popular[0] == product1
        assert popular[1] == product2

    def test_get_similar_products(self, product1, product2, product3):
        similar = get_similar_products(product1, limit=2)
        assert len(similar) > 0
        assert similar[0] == product2
        assert getattr(similar[0], "recommendation_score", 0) > 0

    def test_get_recommendations_unauthenticated(self, product1, product2):
        product1.purchases_count = 10
        product1.save()

        class AnonUser:
            is_authenticated = False

        recs, type_str = get_recommendations_for_user(AnonUser())
        assert type_str == "popular_fallback"
        assert len(recs) > 0
        assert recs[0] == product1

    def test_get_recommendations_personalized(self, user, product1, product2, product3):
        # Пользователь посмотрел product1
        ProductViewHistory.objects.create(user=user, product=product1)

        # Система должна порекомендовать ему похожий product2
        recs, type_str = get_recommendations_for_user(user)
        
        assert type_str == "personalized"
        assert product2 in recs
        assert len(recs) > 0
