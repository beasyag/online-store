# MarketFlow

MarketFlow is a full-stack MVP multi-vendor marketplace built with Nuxt 3 and Django REST Framework. It includes buyers, sellers, products, carts, orders, favorites, reviews and a scoring-based recommendation engine that uses browsing, cart, favorites and purchase history.

## Stack

- Frontend: Nuxt 3, Vue 3, Pinia, TailwindCSS
- Backend: Python 3, Django, DRF, SimpleJWT, PostgreSQL
- Seed data: Faker + custom marketplace-oriented generation


## Local Backend Setup

The backend uses PostgreSQL by default for local application runs. Before running `python manage.py runserver`, create a local environment file from the example and make sure PostgreSQL is running:

```bash
cp backend/.env.example backend/.env

docker compose up -d db redis
cd backend
python manage.py migrate
python manage.py runserver
```

### Docker database credentials


```bash
docker compose down -v
docker compose up --build
```

If you need to keep the data in that volume, create the role/database inside PostgreSQL instead of deleting the volume.

## Tests

Backend tests use `config.test_settings`, which overrides the application database with in-memory SQLite. This keeps `pytest` independent from a running local PostgreSQL server while the normal development/runtime settings continue to use PostgreSQL.

```bash
cd backend
python -m pytest
```

## Production And Secrets Notes

Do not commit real database passwords, Stripe keys or OAuth client IDs. The example env files use placeholders, and `docker-compose.yml` reads sensitive values from `backend/.env`. For production websocket/chat deployments, set `CHANNEL_LAYER_REDIS_URL`; when `DEBUG=False`, the backend refuses to start without a Redis-backed Channels layer. The Google sign-in client ID must be provided through `GOOGLE_CLIENT_ID` for the backend and `NUXT_PUBLIC_GOOGLE_CLIENT_ID` for the frontend.

## User Roles

- Guest: can browse the catalog, open product pages, view sellers and receive popular fallback recommendations.
- Buyer: can register, log in, add items to cart, manage favorites, place orders, leave reviews and receive personalized recommendations.
- Seller: can create a seller profile, publish and edit products, view seller orders and inspect seller dashboard metrics.
- Admin: can moderate and manage data through Django Admin.

## Architecture Overview

1. The repository is split into independent `frontend` and `backend` applications to keep UI and API concerns separated.
2. The frontend is built with Nuxt 3 and Vue 3, using pages, components, composables and Pinia stores for UI state and API interaction.
3. The backend is built as a modular Django project where each domain area lives in its own app: `users`, `sellers`, `products`, `cart`, `orders`, `reviews`, `favorites`, `recommendations`.
4. Authentication is implemented with JWT via SimpleJWT, while profile and role-specific behavior are exposed through DRF endpoints.
5. The catalog domain is centered around products, categories, tags and seller offers, with filtering, popularity sorting, deal/new sections and product detail pages.
6. Buyer activity is captured through view history, favorites, cart state and purchases, and these signals feed the recommendation logic.
7. Recommendation generation is explainable and score-based rather than ML-based, combining similarity and popularity into a final ranking.
8. Order creation is transactional and creates a marketplace order from cart contents while validating availability and updating stock.
9. Seed scripts generate realistic marketplace data so the project can be demonstrated with populated catalogs, sellers, orders and recommendation signals.

## Personal Contribution

This project was implemented as a full-stack MVP with personal responsibility for the key product and engineering decisions:

- designed the marketplace domain model for buyers, sellers, products, carts, orders, favorites and reviews;
- implemented the Django REST API, authentication flow and seller/buyer role behavior;
- built the Nuxt 3 frontend with catalog, auth, cart, favorites, account and seller pages;
- implemented the personalized recommendation engine based on browsing, cart, favorites and purchase history;
- created seed data generation for large demo datasets and realistic recommendation scenarios;
- connected frontend and backend into a working end-to-end marketplace demo.

## Project Structure

```text
backend/
  config/
  users/
  sellers/
  products/
  cart/
  orders/
  reviews/
  favorites/
  recommendations/
frontend/
  assets/
  components/
  composables/
  layouts/
  pages/
  plugins/
  stores/
  types/
```

## Backend Apps

- `users`: custom `User`, registration, login, JWT profile endpoint
- `sellers`: `SellerProfile`, seller storefront endpoints, seller dashboard
- `products`: categories, tags, products, catalog filtering, product detail, product view history
- `cart`: buyer cart and cart items
- `orders`: multi-vendor order creation and seller-side order visibility
- `reviews`: product reviews and ratings
- `favorites`: favorite toggle and favorites list
- `recommendations`: personalized, popular and similar product logic

## Recommendation Logic

The project uses a lightweight scoring-based recommendation approach instead of ML.

Base similarity between two products:

- `+3` if the category matches
- `+2` if the price is close
- `+2` if tags overlap

User signal weights:

- `+4` for similarity to viewed products
- `+5` for similarity to purchased products
- `+3` for similarity to favorites
- `+3` for similarity to items currently in cart
- `+0..2` popularity bonus from purchases, views and average rating

Rules:

- purchased products are excluded from personalized output
- duplicate products are removed
- results are sorted by final score
- anonymous users fall back to popular products

## MVP Scope And Limitations

This repository is intentionally an MVP and has a few known limitations:

- PostgreSQL is used by default; the current setup is intended for MVP/demo usage, not production traffic.
- Payments, shipment integration, refunds and inventory reservation are not implemented.
- Recommendation logic is rule-based and explainable, but it is not a machine-learning system.
- The project prioritizes core marketplace flows over advanced operational features such as notifications, analytics pipelines and audit logs.
- Production deployment settings, observability and scaling concerns are not the main focus of the current version.
- Test coverage is limited and should be expanded before treating the project as production-ready.

## Main API Endpoints

Auth:

- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/auth/refresh/`
- `GET /api/auth/profile/`

Catalog:

- `GET /api/products/`
- `GET /api/products/{id}/`
- `POST /api/products/`
- `PUT /api/products/{id}/`
- `DELETE /api/products/{id}/`
- `GET /api/products/{id}/similar/`
- `GET /api/products/popular/`
- `GET /api/products/new/`
- `GET /api/categories/`
- `GET /api/tags/`

Seller:

- `GET /api/sellers/`
- `GET /api/sellers/{id}/`
- `GET /api/sellers/{id}/products/`
- `GET /api/seller/profile/`
- `POST /api/seller/profile/`
- `PUT /api/seller/profile/`
- `GET /api/seller/dashboard/`

Cart:

- `GET /api/cart/`
- `POST /api/cart/add/`
- `PATCH /api/cart/item/{id}/`
- `DELETE /api/cart/item/{id}/`

Orders:

- `POST /api/orders/create/`
- `GET /api/orders/`
- `GET /api/orders/{id}/`
- `GET /api/orders/seller/`
- `GET /api/orders/seller/{id}/`

Reviews:

- `GET /api/products/{id}/reviews/`
- `POST /api/products/{id}/reviews/`

Favorites:

- `GET /api/favorites/`
- `POST /api/favorites/toggle/`

Recommendations:

- `GET /api/recommendations/`

## Example API Responses

`GET /api/products/`

```json
{
  "count": 1000,
  "next": "http://127.0.0.1:8000/api/products/?page=2",
  "previous": null,
  "results": [
    {
      "id": 12,
      "name": "Nova Smartphone Pro",
      "slug": "nova-smartphone-pro-12",
      "price": "899.00",
      "old_price": "1049.00",
      "image_url": "https://picsum.photos/seed/product-12/800/800",
      "stock": 19,
      "category": {
        "id": 1,
        "name": "Electronics",
        "slug": "electronics"
      },
      "seller": {
        "id": 4,
        "shop_name": "North Peak Store 4",
        "avatar": "https://picsum.photos/seed/shop-4/240/240"
      },
      "tags": [
        { "id": 1, "name": "wireless", "slug": "wireless" },
        { "id": 2, "name": "premium", "slug": "premium" }
      ],
      "average_rating": 4.6,
      "reviews_count": 24,
      "views_count": 315,
      "purchases_count": 87,
      "created_at": "2026-02-07T13:14:00Z",
      "is_favorite": false
    }
  ]
}
```

`GET /api/recommendations/`

```json
{
  "strategy": "personalized",
  "results": [
    {
      "id": 77,
      "name": "Pulse Smartwatch Max",
      "slug": "pulse-smartwatch-max-77",
      "price": "349.00",
      "old_price": null,
      "category": {
        "id": 1,
        "name": "Electronics",
        "slug": "electronics"
      },
      "seller": {
        "id": 9,
        "shop_name": "Urban Tech Store 9",
        "avatar": "https://picsum.photos/seed/shop-9/240/240"
      },
      "average_rating": 4.7,
      "reviews_count": 18,
      "views_count": 241,
      "purchases_count": 64,
      "tags": [
        { "id": 3, "name": "smart", "slug": "smart" },
        { "id": 4, "name": "portable", "slug": "portable" }
      ],
      "is_favorite": false
    }
  ]
}
```

`GET /api/seller/dashboard/`

```json
{
  "product_count": 23,
  "orders_count": 61,
  "sales_count": 118,
  "total_sales": "14238.00",
  "top_products": [],
  "recent_orders": []
}
```

## Personalized Recommendation Examples

- User viewed several electronics items, added headphones to cart and favorited a smartwatch: the engine boosts electronics with overlapping tags such as `wireless`, `smart` and a similar price band.
- User bought running shoes and a yoga mat: the engine promotes sports products with matching tags and adjacent price range while excluding already purchased items.
- Anonymous user: `/api/recommendations/` returns the current popular-product fallback.

## Run From Scratch

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd online-store
```

### 2. Start the backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver
```

Backend default URL: `http://127.0.0.1:8000`

### 3. Start the frontend

```bash
cd frontend
copy .env.example .env
npm install
npm run dev
```

Frontend default URL: `http://localhost:3000`

### 4. Optional: seed demo data

```bash
cd backend
python manage.py seed_data --products 120 --sellers 12 --buyers 30 --orders 45 --clear
```

After seed:

- admin credentials: `admin / admin12345`
- sellers and buyers password: `market12345`

## Demo Scenario

Use this sequence for a short live demonstration of the MVP:

1. Register a buyer account on the frontend and log in.
2. Open the catalog, show product cards, discounts, popularity/new badges and the product detail page.
3. Add one or two products to favorites and cart.
4. Open the cart page, update quantity and create an order.
5. Show order history and explain the order status block.
6. Return to the home page and show the personalized recommendation section with the "why recommended" explanation.
7. Log in as a seller account or create a seller profile.
8. Open the seller dashboard, explain key metrics, top products and recent seller order activity.
9. Open seller product management pages and show product creation/editing flow if needed.

## Seed Large Test Data

```bash
cd backend
python manage.py seed_data --products 1000 --sellers 50 --buyers 200 --orders 500 --clear
```

Smaller smoke-run example:

```bash
python manage.py seed_data --products 120 --sellers 12 --buyers 30 --orders 45 --clear
```

Seed behavior:

- creates `1` admin user
- creates the requested sellers and buyers
- distributes products across sellers
- generates category-aware names, prices and descriptions
- creates uneven popularity, views, favorites and reviews
- creates multi-vendor orders with `1-5` items each
- fills a subset of buyer carts

Default credentials after seed:

- admin: `admin / admin12345`
- sellers and buyers: password `market12345`

## Notes

- The repository intentionally keeps frontend and backend separated.
- SQLite is used by default for a frictionless MVP setup.
- The recommendation system is deliberately explainable and extendable rather than random.
- Django Admin handles moderation and operational management for users, sellers, categories, tags, products, orders and reviews.
