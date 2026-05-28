import pytest
from collections import Counter
from decimal import Decimal
from django.contrib.auth import get_user_model
from products.models import Product, Category, Tag, ProductViewHistory
from sellers.models import SellerProfile
from orders.models import Order, OrderItem
from recommendations.services import (
    base_similarity_score,
    popularity_bonus,
    get_popular_products,
    get_similar_products,
    get_recommendations_for_user,
    get_trending_products,
    get_also_bought_products,
    trending_score,
    _co_purchased_product_ids,
    _time_decay_factor,
    _enforce_diversity,
)

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", email="testuser@example.com", password="testpassword")


@pytest.fixture
def user2(db):
    return User.objects.create_user(username="testuser2", email="testuser2@example.com", password="testpassword")


@pytest.fixture
def seller(db, user):
    return SellerProfile.objects.create(user=user, shop_name="Test Shop")


@pytest.fixture
def seller2(db, user2):
    return SellerProfile.objects.create(user=user2, shop_name="Shop Two")


@pytest.fixture
def category(db):
    return Category.objects.create(name="Electronics", slug="electronics")


@pytest.fixture
def category2(db):
    return Category.objects.create(name="Books", slug="books")


@pytest.fixture
def category3(db):
    return Category.objects.create(name="Clothes", slug="clothes")


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


@pytest.fixture
def product4(db, seller2, category3):
    return Product.objects.create(
        seller=seller2,
        name="T-Shirt",
        slug="t-shirt",
        category=category3,
        price=Decimal("30.00"),
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
        ProductViewHistory.objects.create(user=user, product=product1)

        recs, type_str = get_recommendations_for_user(user)

        assert type_str == "personalized"
        assert product2 in recs
        assert len(recs) > 0


@pytest.mark.django_db
class TestTimeDecay:
    def test_decay_factor_zero_days(self):
        factor = _time_decay_factor(0)
        assert factor == 1.0

    def test_decay_factor_half_life(self):
        factor = _time_decay_factor(14)
        assert abs(factor - 0.5) < 0.01

    def test_decay_factor_decreases(self):
        assert _time_decay_factor(1) > _time_decay_factor(7) > _time_decay_factor(30)


@pytest.mark.django_db
class TestCollaborativeFiltering:
    def test_co_purchased_product_ids(self, user, user2, seller, category, product1, product2, product3):
        order1 = Order.objects.create(user=user, total_amount=Decimal("200"))
        OrderItem.objects.create(order=order1, product=product1, seller=seller, quantity=1, price_at_purchase=Decimal("100"))
        OrderItem.objects.create(order=order1, product=product2, seller=seller, quantity=1, price_at_purchase=Decimal("105"))

        order2 = Order.objects.create(user=user2, total_amount=Decimal("150"))
        OrderItem.objects.create(order=order2, product=product1, seller=seller, quantity=1, price_at_purchase=Decimal("100"))
        OrderItem.objects.create(order=order2, product=product3, seller=seller, quantity=1, price_at_purchase=Decimal("50"))

        co_ids = _co_purchased_product_ids({product1.id}, {product1.id})
        assert product2.id in co_ids
        assert product3.id in co_ids

    def test_also_bought_returns_products(self, user, user2, seller, category, product1, product2, product3):
        order1 = Order.objects.create(user=user, total_amount=Decimal("200"))
        OrderItem.objects.create(order=order1, product=product1, seller=seller, quantity=1, price_at_purchase=Decimal("100"))
        OrderItem.objects.create(order=order1, product=product2, seller=seller, quantity=1, price_at_purchase=Decimal("105"))

        result = get_also_bought_products(product1, limit=4)
        assert len(result) > 0

    def test_also_bought_falls_back_to_similar(self, product1, product2):
        result = get_also_bought_products(product1, limit=4)
        assert isinstance(result, list)


@pytest.mark.django_db
class TestTrending:
    def test_trending_score_no_orders(self, product1):
        assert trending_score(product1) == 0.0

    def test_trending_score_with_recent_orders(self, user, seller, product1):
        order = Order.objects.create(user=user, total_amount=Decimal("100"))
        OrderItem.objects.create(order=order, product=product1, seller=seller, quantity=1, price_at_purchase=Decimal("100"))
        product1.purchases_count = 1
        product1.save()

        score = trending_score(product1)
        assert score > 0

    def test_get_trending_products(self, user, seller, product1, product2):
        order = Order.objects.create(user=user, total_amount=Decimal("100"))
        OrderItem.objects.create(order=order, product=product1, seller=seller, quantity=1, price_at_purchase=Decimal("100"))
        product1.purchases_count = 1
        product1.save()

        trending = get_trending_products(limit=4)
        assert isinstance(trending, list)


@pytest.mark.django_db
class TestDiversityEnforcement:
    def test_enforce_diversity_limits_category(self, seller, seller2, category, category2, tag1):
        products = []
        for i in range(8):
            s = seller if i % 2 == 0 else seller2
            p = Product.objects.create(
                seller=s, name=f"Gadget {i}", slug=f"gadget-{i}",
                category=category, price=Decimal("100"), is_active=True,
            )
            p.recommendation_score = 10.0 - i
            products.append(p)

        other = Product.objects.create(
            seller=seller2, name="Book A", slug="book-a",
            category=category2, price=Decimal("20"), is_active=True,
        )
        other.recommendation_score = 1.0
        products.append(other)

        result = _enforce_diversity(products, limit=6)
        cat_counts = Counter(p.category_id for p in result)
        assert other in result, "Diversity should include items from other categories"

    def test_enforce_diversity_no_duplicates(self, seller, category):
        p1 = Product.objects.create(
            seller=seller, name="Item A", slug="item-a",
            category=category, price=Decimal("50"), is_active=True,
        )
        p1.recommendation_score = 5.0
        result = _enforce_diversity([p1, p1], limit=4)
        assert len(result) == 1


@pytest.mark.django_db
class TestPersonalizedWithCollaborative:
    def test_collaborative_signals_in_personalized(self, user, user2, seller, category, product1, product2, product3):
        ProductViewHistory.objects.create(user=user, product=product1)

        order1 = Order.objects.create(user=user2, total_amount=Decimal("200"))
        OrderItem.objects.create(order=order1, product=product1, seller=seller, quantity=1, price_at_purchase=Decimal("100"))
        OrderItem.objects.create(order=order1, product=product3, seller=seller, quantity=1, price_at_purchase=Decimal("50"))

        recs, strategy = get_recommendations_for_user(user, limit=12)
        assert strategy == "personalized"
        assert len(recs) > 0
