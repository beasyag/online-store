import random
from collections import Counter
from datetime import timedelta
from decimal import Decimal
from urllib.parse import quote

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from faker import Faker

from cart.models import Cart, CartItem
from favorites.models import Favorite
from orders.models import Order, OrderItem
from products.models import Category, Product, ProductViewHistory, Tag
from reviews.models import Review
from sellers.models import SellerProfile

User = get_user_model()

DEFAULT_PASSWORD = "market12345"

CATEGORY_SPECS = {
    "Электроника": {"slug": "electronics"},
    "Игрушки": {"slug": "toys"},
    "Одежда": {"slug": "clothing"},
    "Обувь": {"slug": "shoes"},
    "Аксессуары": {"slug": "accessories"},
    "Товары для дома": {"slug": "home"},
    "Красота": {"slug": "beauty"},
    "Спорт": {"slug": "sports"},
    "Книги": {"slug": "books"},
}

PRODUCT_LIBRARY = [
    {"code": "iphone-15-pro", "category": "Электроника", "name": "Apple iPhone 15 Pro 256GB", "price": 599000, "image": "iphone,smartphone", "tags": ["apple", "iphone", "smartphone", "premium"], "weight": 96},
    {"code": "galaxy-s24", "category": "Электроника", "name": "Samsung Galaxy S24 256GB", "price": 459000, "image": "samsung,smartphone", "tags": ["samsung", "smartphone", "android", "premium"], "weight": 90},
    {"code": "macbook-air-m2", "category": "Электроника", "name": "Apple MacBook Air M2 13", "price": 689000, "image": "macbook,laptop", "tags": ["apple", "laptop", "office", "premium"], "weight": 84},
    {"code": "playstation-5", "category": "Электроника", "name": "Sony PlayStation 5 Slim", "price": 309000, "image": "playstation,console", "tags": ["gaming", "console", "popular", "premium"], "weight": 82},
    {"code": "airpods-pro-2", "category": "Электроника", "name": "Apple AirPods Pro 2", "price": 149000, "image": "airpods,earbuds", "tags": ["apple", "audio", "wireless", "premium"], "weight": 78},
    {"code": "lego-city", "category": "Игрушки", "name": "LEGO City Полицейский участок", "price": 58900, "image": "lego,toy", "tags": ["lego", "toy", "kids", "gift"], "weight": 88},
    {"code": "barbie-house", "category": "Игрушки", "name": "Barbie Dreamhouse", "price": 67900, "image": "barbie,dollhouse", "tags": ["toy", "barbie", "kids", "gift"], "weight": 70},
    {"code": "hot-wheels", "category": "Игрушки", "name": "Hot Wheels Track Builder", "price": 23900, "image": "hotwheels,toycar", "tags": ["toy", "car", "kids", "popular"], "weight": 66},
    {"code": "teddy-bear", "category": "Игрушки", "name": "Большой плюшевый мишка XL", "price": 15900, "image": "teddy,bear,toy", "tags": ["toy", "kids", "gift", "soft"], "weight": 58},
    {"code": "nike-hoodie", "category": "Одежда", "name": "Nike Club Fleece Hoodie", "price": 34900, "image": "hoodie,fashion", "tags": ["fashion", "casual", "sport", "popular"], "weight": 67},
    {"code": "nike-air-force-1", "category": "Обувь", "name": "Nike Air Force 1", "price": 64900, "image": "nike,sneakers", "tags": ["shoes", "nike", "casual", "popular"], "weight": 86},
    {"code": "adidas-gazelle", "category": "Обувь", "name": "Adidas Gazelle", "price": 55900, "image": "adidas,sneakers", "tags": ["shoes", "adidas", "casual", "classic"], "weight": 72},
    {"code": "samsonite-backpack", "category": "Аксессуары", "name": "Samsonite City Backpack", "price": 47900, "image": "backpack,bag", "tags": ["travel", "office", "daily", "premium"], "weight": 58},
    {"code": "xiaomi-powerbank", "category": "Аксессуары", "name": "Xiaomi Power Bank 20000 mAh", "price": 16900, "image": "powerbank,charger", "tags": ["xiaomi", "portable", "travel", "daily"], "weight": 68},
    {"code": "dyson-v8", "category": "Товары для дома", "name": "Dyson V8 Absolute", "price": 279000, "image": "vacuum,home", "tags": ["home-gadget", "premium", "cleaning", "popular"], "weight": 66},
    {"code": "airfryer", "category": "Товары для дома", "name": "Philips Airfryer Essential", "price": 119000, "image": "airfryer,kitchen", "tags": ["kitchen", "home-gadget", "family", "popular"], "weight": 61},
    {"code": "cerave-cream", "category": "Красота", "name": "CeraVe Moisturizing Cream", "price": 10900, "image": "skincare,cream", "tags": ["skincare", "hydration", "daily", "care"], "weight": 73},
    {"code": "dior-sauvage", "category": "Красота", "name": "Dior Sauvage EDT 100ml", "price": 67900, "image": "perfume,bottle", "tags": ["perfume", "gift", "premium", "popular"], "weight": 56},
    {"code": "yoga-mat", "category": "Спорт", "name": "Premium Yoga Mat 6mm", "price": 16900, "image": "yoga,mat", "tags": ["fitness", "home-workout", "daily", "lightweight"], "weight": 52},
    {"code": "atomic-habits", "category": "Книги", "name": "Джеймс Клир: Атомные привычки", "price": 7900, "image": "book,selfhelp", "tags": ["books", "learning", "non-fiction", "popular"], "weight": 66},
    {"code": "harry-potter", "category": "Книги", "name": "Гарри Поттер. Подарочный комплект", "price": 35900, "image": "books,harrypotter", "tags": ["books", "bestseller", "fiction", "gift"], "weight": 70},
]


class Command(BaseCommand):
    help = "Заполняет маркетплейс реалистичными демонстрационными данными."

    def add_arguments(self, parser):
        parser.add_argument("--products", type=int, default=1000)
        parser.add_argument("--sellers", type=int, default=50)
        parser.add_argument("--buyers", type=int, default=200)
        parser.add_argument("--orders", type=int, default=500)
        parser.add_argument("--clear", action="store_true")

    def handle(self, *args, **options):
        random.seed(42)
        Faker.seed(42)
        self.fake = Faker("ru_RU")

        with transaction.atomic():
            if options["clear"]:
                self._clear_existing_data()

            self._ensure_admin()
            categories, tags_by_name = self._seed_catalog_taxonomy()
            sellers = self._seed_sellers(options["sellers"])
            buyers = self._seed_buyers(options["buyers"])
            products, product_weights, original_stock = self._seed_products(categories, tags_by_name, sellers, options["products"])
            purchase_counts = self._seed_orders(products, product_weights, buyers, options["orders"])
            view_counts = self._seed_view_history(products, product_weights, buyers, options["products"])
            self._seed_reviews(products, product_weights, buyers, options["products"])
            self._seed_favorites(products, product_weights, buyers, options["products"])
            self._seed_carts(products, product_weights, buyers)
            self._apply_product_stats(products, original_stock, purchase_counts, view_counts)

        self.stdout.write(self.style.SUCCESS("Демонстрационные данные маркетплейса успешно сгенерированы."))
        self.stdout.write("Администратор: username=admin password=admin12345")
        self.stdout.write(f"Пароль для сгенерированных продавцов и покупателей: {DEFAULT_PASSWORD}")

    def _clear_existing_data(self):
        CartItem.objects.all().delete()
        Cart.objects.all().delete()
        Favorite.objects.all().delete()
        Review.objects.all().delete()
        ProductViewHistory.objects.all().delete()
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        Product.tags.through.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        Tag.objects.all().delete()
        SellerProfile.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

    def _ensure_admin(self):
        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@example.com", "role": User.Role.ADMIN, "is_staff": True, "is_superuser": True},
        )
        if created:
            admin.set_password("admin12345")
            admin.save()

    def _seed_catalog_taxonomy(self):
        categories = {}
        tags_by_name = {}
        all_tags = sorted({tag for template in PRODUCT_LIBRARY for tag in template["tags"]})
        for category_name, spec in CATEGORY_SPECS.items():
            category, _ = Category.objects.get_or_create(name=category_name, defaults={"slug": spec["slug"]})
            categories[category_name] = category
        for tag_name in all_tags:
            tag, _ = Tag.objects.get_or_create(name=tag_name, defaults={"slug": slugify(tag_name)})
            tags_by_name[tag_name] = tag
        return categories, tags_by_name

    def _seed_sellers(self, count):
        existing = SellerProfile.objects.count()
        sellers = []
        for index in range(count):
            absolute_index = existing + index + 1
            user = User.objects.create_user(
                username=f"seller{absolute_index}",
                email=f"seller{absolute_index}@market.local",
                password=DEFAULT_PASSWORD,
                role=User.Role.SELLER,
                first_name=self.fake.first_name(),
                last_name=self.fake.last_name(),
            )
            sellers.append(
                SellerProfile.objects.create(
                    user=user,
                    shop_name=f"{self.fake.company()} Маркет {absolute_index}",
                    description=self.fake.text(max_nb_chars=180),
                    avatar=f"https://loremflickr.com/320/320/store?lock={absolute_index}",
                )
            )
        return sellers

    def _seed_buyers(self, count):
        existing_buyers = User.objects.filter(role=User.Role.BUYER).count()
        buyers = []
        for index in range(count):
            absolute_index = existing_buyers + index + 1
            buyers.append(
                User.objects.create_user(
                    username=f"buyer{absolute_index}",
                    email=f"buyer{absolute_index}@market.local",
                    password=DEFAULT_PASSWORD,
                    role=User.Role.BUYER,
                    first_name=self.fake.first_name(),
                    last_name=self.fake.last_name(),
                )
            )
        return buyers

    def _seed_products(self, categories, tags_by_name, sellers, count):
        product_payloads = []
        through_rows = []
        through_model = Product.tags.through
        now = timezone.now()
        existing_count = Product.objects.count()
        used_pairs = set()
        attempts = 0
        capacity = len(sellers) * len(PRODUCT_LIBRARY)
        allow_duplicates = count > capacity

        while len(product_payloads) < count and attempts < count * 20:
            attempts += 1
            template = random.choices(PRODUCT_LIBRARY, weights=[item["weight"] for item in PRODUCT_LIBRARY], k=1)[0]
            seller = random.choice(sellers)
            pair_key = (seller.id, template["code"])
            if not allow_duplicates and pair_key in used_pairs:
                continue
            used_pairs.add(pair_key)

            category = categories[template["category"]]
            created_at = now - timedelta(days=random.randint(0, 180), hours=random.randint(0, 23))
            price = self._offer_price(template["price"])
            old_price = self._old_price(price)
            product_slug = f"{template['code']}-{seller.id}-{existing_count + len(product_payloads) + 1}"
            weight = float(template["weight"] * (0.35 + min(1.0, (now - created_at).days / 180)))

            product_payloads.append(
                {
                    "slug": product_slug,
                    "product": Product(
                        seller=seller,
                        category=category,
                        name=template["name"],
                        slug=product_slug,
                        offer_group=template["code"],
                        description=self._product_description(template["name"], template["category"]),
                        price=price,
                        old_price=old_price,
                        image_url=self._image_url(template["image"], template["code"]),
                        stock=self._stock_for_category(category.slug),
                        is_active=random.random() > 0.02,
                        created_at=created_at,
                        updated_at=created_at,
                    ),
                    "tag_names": template["tags"],
                    "weight": weight,
                }
            )

        Product.objects.bulk_create([payload["product"] for payload in product_payloads], batch_size=500)
        created_products = {
            product.slug: product
            for product in Product.objects.filter(slug__in=[payload["slug"] for payload in product_payloads]).select_related("category", "seller")
        }

        weights = {}
        original_stock = {}
        for payload in product_payloads:
            product = created_products[payload["slug"]]
            weights[product.id] = payload["weight"]
            original_stock[product.id] = product.stock
            for tag_name in payload["tag_names"]:
                through_rows.append(through_model(product_id=product.id, tag_id=tags_by_name[tag_name].id))

        through_model.objects.bulk_create(through_rows, ignore_conflicts=True, batch_size=1000)
        created_ids = [product.id for product in created_products.values()]
        products = list(Product.objects.filter(id__in=created_ids).select_related("category", "seller"))
        return products, weights, original_stock

    def _seed_orders(self, products, product_weights, buyers, order_count):
        purchase_counts = Counter()
        weighted_products = self._weighted_lists(products, product_weights)
        statuses = [Order.Status.COMPLETED, Order.Status.SHIPPED, Order.Status.PROCESSING, Order.Status.CANCELED]
        status_weights = [0.48, 0.24, 0.22, 0.06]
        now = timezone.now()
        order_items = []

        for _ in range(order_count):
            user = random.choice(buyers)
            created_at = now - timedelta(days=random.randint(0, 120), hours=random.randint(0, 23))
            order = Order.objects.create(user=user, total_amount=Decimal("0.00"), status=random.choices(statuses, weights=status_weights, k=1)[0])
            total = Decimal("0.00")
            for product in self._pick_unique_products(products, weighted_products, random.randint(1, 5)):
                quantity = random.randint(1, 2 if product.category.slug == "books" else 3)
                order_items.append(OrderItem(order=order, product=product, seller=product.seller, quantity=quantity, price_at_purchase=product.price))
                purchase_counts[product.id] += quantity
                total += Decimal(product.price) * quantity
            Order.objects.filter(pk=order.pk).update(total_amount=total, created_at=created_at, updated_at=created_at)

        OrderItem.objects.bulk_create(order_items, batch_size=1000)
        return purchase_counts

    def _seed_view_history(self, products, product_weights, buyers, product_count):
        target = max(product_count * 10, 10000 if product_count >= 1000 else product_count * 6)
        weighted_products = self._weighted_lists(products, product_weights)
        view_counts = Counter()
        history_rows = []
        now = timezone.now()

        for _ in range(target):
            user = random.choice(buyers)
            product = random.choices(weighted_products["products"], weights=weighted_products["weights"], k=1)[0]
            viewed_at = now - timedelta(days=random.randint(0, 90), hours=random.randint(0, 23), minutes=random.randint(0, 59))
            history_rows.append(ProductViewHistory(user=user, product=product, viewed_at=viewed_at))
            view_counts[product.id] += 1

        ProductViewHistory.objects.bulk_create(history_rows, batch_size=2000)
        return view_counts

    def _seed_reviews(self, products, product_weights, buyers, product_count):
        target = max(product_count * 2, 2000 if product_count >= 1000 else product_count)
        weighted_products = self._weighted_lists(products, product_weights)
        created_pairs = set()
        review_rows = []
        attempts = 0

        while len(review_rows) < target and attempts < target * 8:
            attempts += 1
            buyer = random.choice(buyers)
            product = random.choices(weighted_products["products"], weights=weighted_products["weights"], k=1)[0]
            pair = (buyer.id, product.id)
            if pair in created_pairs:
                continue
            created_pairs.add(pair)
            high_weight = product_weights.get(product.id, 1) >= 65
            rating = random.choices([5, 4, 3, 2, 1], weights=[0.42, 0.31, 0.17, 0.07, 0.03] if high_weight else [0.24, 0.28, 0.23, 0.15, 0.10], k=1)[0]
            created_at = max(product.created_at, timezone.now() - timedelta(days=random.randint(0, 90)))
            review_rows.append(Review(user=buyer, product=product, rating=rating, text=self._review_text(rating, product.name), created_at=created_at))

        Review.objects.bulk_create(review_rows, batch_size=1000)

    def _seed_favorites(self, products, product_weights, buyers, product_count):
        target = max(product_count * 3, 3000 if product_count >= 1000 else product_count * 2)
        weighted_products = self._weighted_lists(products, product_weights)
        favorite_rows = []
        created_pairs = set()
        attempts = 0

        while len(favorite_rows) < target and attempts < target * 8:
            attempts += 1
            buyer = random.choice(buyers)
            product = random.choices(weighted_products["products"], weights=weighted_products["weights"], k=1)[0]
            pair = (buyer.id, product.id)
            if pair in created_pairs:
                continue
            created_pairs.add(pair)
            favorite_rows.append(Favorite(user=buyer, product=product, created_at=timezone.now() - timedelta(days=random.randint(0, 60))))

        Favorite.objects.bulk_create(favorite_rows, batch_size=1000)

    def _seed_carts(self, products, product_weights, buyers):
        weighted_products = self._weighted_lists(products, product_weights)
        for buyer in random.sample(buyers, k=max(1, len(buyers) // 4)):
            cart = Cart.objects.create(user=buyer)
            cart_items = []
            for product in self._pick_unique_products(products, weighted_products, random.randint(1, 4)):
                cart_items.append(CartItem(cart=cart, product=product, quantity=random.randint(1, 2 if product.category.slug == "books" else 3)))
            CartItem.objects.bulk_create(cart_items, batch_size=100)

    def _apply_product_stats(self, products, original_stock, purchase_counts, view_counts):
        for product in products:
            product.purchases_count = purchase_counts[product.id]
            product.views_count = view_counts[product.id]
            product.stock = max(0, original_stock[product.id] - purchase_counts[product.id])
        Product.objects.bulk_update(products, ["purchases_count", "views_count", "stock"], batch_size=500)

    def _weighted_lists(self, products, product_weights):
        return {"products": products, "weights": [max(1, int(product_weights[product.id])) for product in products]}

    def _pick_unique_products(self, all_products, weighted_products, count):
        chosen = []
        used_groups = set()
        attempts = 0
        while len(chosen) < count and attempts < len(all_products) * 5:
            attempts += 1
            product = random.choices(weighted_products["products"], weights=weighted_products["weights"], k=1)[0]
            group_key = product.offer_group or f"id-{product.id}"
            if group_key in used_groups:
                continue
            used_groups.add(group_key)
            chosen.append(product)
        return chosen

    def _offer_price(self, base_price):
        return (Decimal(str(base_price)) * Decimal(str(random.uniform(0.92, 1.18)))).quantize(Decimal("0.01"))

    def _old_price(self, price):
        if random.random() >= 0.58:
            return None
        return (price * Decimal(str(random.uniform(1.07, 1.28)))).quantize(Decimal("0.01"))

    def _stock_for_category(self, category_slug):
        if category_slug == "electronics":
            return random.randint(4, 18)
        if category_slug == "toys":
            return random.randint(8, 40)
        if category_slug == "books":
            return random.randint(6, 28)
        if category_slug == "home":
            return random.randint(4, 20)
        return random.randint(8, 55)

    def _product_description(self, product_name, category_name):
        lines = {
            "Электроника": "Популярная техника для работы, развлечений и повседневного использования.",
            "Игрушки": "Подарочный и игровой товар с понятной подачей для родителей и детей.",
            "Одежда": "Удобная городская модель на каждый день с актуальным силуэтом.",
            "Обувь": "Практичная пара для города и повседневной носки.",
            "Аксессуары": "Полезный аксессуар для поездок, работы и ежедневного использования.",
            "Товары для дома": "Товар для комфорта дома, кухни или быстрой бытовой рутины.",
            "Красота": "Средство для ухода или подарок с понятным позиционированием.",
            "Спорт": "Позиция для тренировок, активности дома или на улице.",
            "Книги": "Издание, которое хорошо смотрится в каталоге и часто попадает в рекомендации.",
        }
        return f"{product_name}. {lines[category_name]} {random.choice(['Хорошо подходит для витрины маркетплейса.', 'Часто покупают и добавляют в избранное.', 'Подходит для демонстрации скидок и рекомендаций.'])}"

    def _review_text(self, rating, product_name):
        variants = {
            5: [f"{product_name} полностью оправдал ожидания.", f"Очень удачная покупка: {product_name} понравился сразу."],
            4: [f"{product_name} хороший, описание совпадает.", f"Нормальная цена и достойное качество у {product_name}."],
            3: [f"{product_name} обычный товар без сюрпризов.", f"Средний опыт использования {product_name}, есть и плюсы, и минусы."],
            2: [f"{product_name} ожидал большего за такую цену.", f"Есть заметные минусы у товара {product_name}."],
            1: [f"{product_name} не оправдал ожиданий.", f"Качество {product_name} оказалось слабым."],
        }
        return random.choice(variants[rating])

    def _image_url(self, query_value, key):
        encoded = quote(query_value, safe=",")
        return f"https://loremflickr.com/900/900/{encoded}?lock={abs(hash(key)) % 10000}"
