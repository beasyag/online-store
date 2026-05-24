# MarketFlow

MarketFlow - MVP многопродавцового маркетплейса на Nuxt 3 и Django REST Framework. Проект покрывает основные сценарии онлайн-магазина: каталог товаров, регистрацию и вход, роли покупателя и продавца, корзину, заказы, избранное, отзывы, чат, оплату через Stripe и персональные рекомендации.

## Стек

- Frontend: Nuxt 3, Vue 3, Pinia, TailwindCSS
- Backend: Python 3, Django 5, Django REST Framework, SimpleJWT
- База данных: PostgreSQL
- Очереди и фоновые задачи: Redis + Celery
- Realtime: Django Channels + Redis
- API-документация: drf-spectacular, Swagger, Redoc
- Платежи: Stripe
- Демо-данные: Faker и кастомная генерация маркетплейса
- Контейнеризация: Docker Compose
- Оркестрация: Kubernetes-манифесты

## Основные возможности

- Каталог товаров с категориями, тегами, продавцами и несколькими предложениями внутри одной товарной группы.
- Поиск по товарам с PostgreSQL full-text search, поиском по началу слова и исправлением английской раскладки на русскую.
- Персональные рекомендации на основе просмотров, корзины, избранного и покупок.
- Регистрация, JWT-авторизация и профиль пользователя.
- Роли: гость, покупатель, продавец, администратор.
- Корзина и оформление multi-vendor заказа.
- Самовывоз, курьерская доставка и выбор пункта выдачи.
- Избранное и отзывы на товары.
- Кабинет продавца, управление товарами и просмотр заказов продавца.
- Чат между покупателем и продавцом.
- Stripe Checkout для онлайн-оплаты.
- Swagger/Redoc документация API.

## Роли пользователей

- Гость: просматривает каталог, товары, продавцов и получает популярные рекомендации.
- Покупатель: регистрируется, входит в аккаунт, добавляет товары в корзину и избранное, оформляет заказы, оставляет отзывы и получает персональные рекомендации.
- Продавец: создает профиль продавца, публикует и редактирует товары, смотрит заказы и метрики в кабинете.
- Администратор: управляет данными через Django Admin.

## Архитектура

Репозиторий разделен на два независимых приложения:

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
  chat/

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

Backend построен как набор Django-приложений по доменным зонам. Frontend построен на Nuxt pages/components/composables/stores. API вызывается через общий `useApiClient`.

## Backend-приложения

- `users` - кастомная модель пользователя, регистрация, вход, JWT, профиль.
- `sellers` - профиль продавца, витрина продавца, dashboard продавца.
- `products` - категории, теги, товары, фильтрация, поиск, похожие товары, история просмотров.
- `cart` - корзина покупателя.
- `orders` - создание заказов, заказы покупателя и продавца, филиалы самовывоза.
- `reviews` - отзывы и рейтинг товаров.
- `favorites` - избранные товары.
- `recommendations` - персональные, популярные и похожие рекомендации.
- `chat` - комнаты и сообщения между покупателем и продавцом.

## Поиск

Поиск работает через `GET /api/products/?q=<запрос>`.

Backend ищет по:

- названию товара;
- описанию;
- тегам;
- категории;
- названию магазина продавца.

Для PostgreSQL используется full-text search с русской конфигурацией. Дополнительно включены:

- поиск по началу слова: `кн` может находить `книга`, `книги`;
- мягкий fallback через `icontains`;
- исправление английской раскладки на русскую: `rybub` дополнительно ищется как `книги`.

Если поисковый запрос активен, выдача сортируется по релевантности, а не только по популярности.

## Рекомендации

Система рекомендаций rule-based, без ML-модели. Она объяснима и подходит для MVP.

Базовая похожесть товаров:

- `+3`, если совпадает категория;
- `+2`, если цена близкая;
- `+2`, если пересекаются теги.

Сигналы пользователя:

- `+4` за похожесть на просмотренные товары;
- `+5` за похожесть на купленные товары;
- `+3` за похожесть на избранное;
- `+3` за похожесть на товары в корзине;
- `+0..2` бонус за популярность, просмотры и рейтинг.

Правила:

- купленные товары исключаются из персональной выдачи;
- дубликаты удаляются;
- результаты сортируются по итоговому score;
- анонимные пользователи получают популярные товары.

## API-документация

После запуска backend:

- Swagger: `http://127.0.0.1:8000/api/docs/`
- Redoc: `http://127.0.0.1:8000/api/redoc/`
- OpenAPI schema: `http://127.0.0.1:8000/api/schema/`

## Основные API endpoints

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

- `GET /api/branches/`
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

Chat:

- `GET /api/chat/rooms/`
- `POST /api/chat/rooms/start/`
- `GET /api/chat/rooms/{id}/messages/`

Payments:

- `POST /api/orders/{id}/checkout/`

## Локальный запуск без Docker

### 1. Backend

Создайте env-файл:

```bash
copy backend\.env.example backend\.env
```

Убедитесь, что PostgreSQL запущен и параметры в `backend/.env` корректны:

```env
DB_ENGINE=postgresql
DB_NAME=store
DB_USER=postgres
DB_PASSWORD=8747
DB_HOST=localhost
DB_PORT=5432
```

Запуск:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Backend: `http://127.0.0.1:8000`

### 2. Frontend

```bash
cd frontend
copy .env.example .env
npm install
npm run dev
```

Frontend: `http://localhost:3000`

## Запуск через Docker Compose

Перед первым запуском создайте `backend/.env`:

```bash
copy backend\.env.example backend\.env
```

Запуск из корня проекта:

```bash
docker compose up --build
```

Сервисы Docker Compose:

- `db` - PostgreSQL, порт `5432`;
- `redis` - Redis для Celery и Channels, порт `6379`;
- `backend` - Django API, порт `8000`;
- `celery` - Celery worker;
- `frontend` - Nuxt dev server, порт `3000`.

Адреса:

- Frontend: `http://localhost:3000`
- Backend: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/api/docs/`

Остановка:

```bash
docker compose down
```

Полный сброс контейнеров и volume базы данных:

```bash
docker compose down -v
docker compose up --build
```

Данные PostgreSQL хранятся в Docker volume:

```text
postgres_data_v2
```

## Демо-данные

Небольшой набор:

```bash
docker compose exec backend python manage.py seed_data --products 120 --sellers 12 --buyers 30 --orders 45 --clear
```

Большой набор:

```bash
docker compose exec backend python manage.py seed_data --products 1000 --sellers 50 --buyers 200 --orders 500 --clear
```

После генерации:

- admin: `admin / admin12345`
- продавцы и покупатели: пароль `market12345`

## Тесты

Backend-тесты используют `config.test_settings`, где база заменяется на in-memory SQLite. Поэтому тесты можно запускать без локального PostgreSQL.

```bash
cd backend
python -m pytest
```

## Kubernetes

Манифесты находятся в папке `kubernetes/`.

Текущие манифесты описывают:

- backend deployment;
- frontend deployment;
- celery deployment;
- redis service;
- backend/frontend services.

Применение:

```bash
kubectl apply -f kubernetes/
```

Важно: перед использованием в реальном кластере нужно заменить `my-registry/marketflow-backend:latest` и `my-registry/marketflow-frontend:latest` на реальные образы в registry, а также настроить PostgreSQL service/secret под окружение.

Удаление ресурсов:

```bash
kubectl delete -f kubernetes/
```

## Переменные окружения

Основные переменные backend:

- `SECRET_KEY` - секрет Django.
- `DEBUG` - режим разработки.
- `ALLOWED_HOSTS` - разрешенные хосты.
- `CORS_ALLOWED_ORIGINS` - frontend origins.
- `DB_ENGINE` - `postgresql` или `sqlite`.
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` - подключение к БД.
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` - инициализация PostgreSQL контейнера.
- `CELERY_BROKER_URL` - broker Celery.
- `CELERY_RESULT_BACKEND` - backend результатов Celery.
- `CHANNEL_LAYER_REDIS_URL` - Redis для Django Channels.
- `GOOGLE_CLIENT_ID` - Google OAuth client ID.
- `STRIPE_SECRET_KEY` - секретный ключ Stripe.
- `FRONTEND_BASE_URL` - адрес frontend для redirect-сценариев.

Основные переменные frontend:

- `NUXT_PUBLIC_API_BASE` - публичный URL backend API.
- `NUXT_PUBLIC_GOOGLE_CLIENT_ID` - Google OAuth client ID для frontend.

## Сценарий демонстрации

1. Открыть главную страницу и показать каталог.
2. Выполнить поиск, включая короткий запрос и пример неправильной раскладки.
3. Открыть карточку товара и показать предложения продавцов.
4. Добавить товар в избранное и корзину.
5. Оформить заказ с доставкой или самовывозом.
6. Показать историю заказов покупателя.
7. Показать блок персональных рекомендаций.
8. Войти как продавец.
9. Открыть кабинет продавца, список товаров и заказы.
10. Показать Swagger-документацию API.

## Ограничения MVP

- Проект предназначен для демонстрации и дипломной работы, а не для production-нагрузки.
- Рекомендации rule-based, без ML-модели.
- Kubernetes-манифесты требуют адаптации под конкретный registry, secrets и ingress.
- Stripe используется как интеграционный сценарий, без полного production billing flow.
- Нужны дополнительные тесты перед production-использованием.

## Безопасность

Не коммитьте реальные секреты:

- пароли БД;
- Stripe secret key;
- Google OAuth client ID;
- production `SECRET_KEY`.

Для production используйте отдельные secrets, HTTPS, отдельную БД, observability и резервное копирование.
