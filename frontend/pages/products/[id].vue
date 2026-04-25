<script setup lang="ts">
import type { PaginatedResponse, Product, Review } from "~/types";
import { useApiClient } from "~/composables/useApiClient";
import { useApiError } from "~/composables/useApiError";
import { useFormatters } from "~/composables/useFormatters";
import { usePaginatedResults } from "~/composables/usePaginatedResults";
import { useAuthStore } from "~/stores/auth";
import { useCartStore } from "~/stores/cart";
import { useFavoritesStore } from "~/stores/favorites";

const route = useRoute();
const api = useApiClient();
const auth = useAuthStore();
const cartStore = useCartStore();
const favoritesStore = useFavoritesStore();
const { getErrorMessage } = useApiError();
const { formatMoney, formatRating, formatCategoryName, formatTagName } = useFormatters();

const reviewForm = reactive({
  rating: 5,
  text: ""
});
const reviewError = ref("");
const reviewSuccess = ref("");
const productLoadError = ref("");

const productId = computed(() => Number(route.params.id));

const { data: product, error: productError, refresh: refreshProduct } = await useAsyncData(
  `product-${productId.value}`,
  () => api.get<Product>(`/products/${productId.value}/`),
  { watch: [productId] }
);
const { data: similarData, refresh: refreshSimilar } = await useAsyncData(
  `similar-${productId.value}`,
  () => api.get<PaginatedResponse<Product>>(`/products/${productId.value}/similar/`),
  { watch: [productId] }
);
const { data: reviewsData, refresh: refreshReviews } = await useAsyncData(
  `reviews-${productId.value}`,
  () => api.get<PaginatedResponse<Review>>(`/products/${productId.value}/reviews/`),
  { watch: [productId] }
);

const similarProducts = computed(() => usePaginatedResults<Product>(similarData.value));
const reviews = computed(() => usePaginatedResults<Review>(reviewsData.value));
const offers = computed(() => product.value?.seller_offers || []);
const isFavorite = computed(() => (product.value ? favoritesStore.ids.has(product.value.id) || product.value.is_favorite : false));

const addToCart = async () => {
  if (!product.value) {
    return;
  }
  if (!auth.loggedIn) {
    return navigateTo("/login");
  }
  try {
    await cartStore.addToCart(product.value.id, 1);
  } catch {}
};

const toggleFavorite = async () => {
  if (!product.value) {
    return;
  }
  if (!auth.loggedIn) {
    return navigateTo("/login");
  }
  try {
    await favoritesStore.toggleFavorite(product.value.id);
    await refreshProduct();
  } catch {}
};

const submitReview = async () => {
  if (!auth.loggedIn || !product.value) {
    return navigateTo("/login");
  }
  reviewError.value = "";
  reviewSuccess.value = "";
  try {
    await api.post(`/products/${product.value.id}/reviews/`, reviewForm);
    reviewForm.rating = 5;
    reviewForm.text = "";
    reviewSuccess.value = "Отзыв успешно добавлен.";
    await Promise.all([refreshReviews(), refreshProduct(), refreshSimilar()]);
  } catch (error: any) {
    reviewError.value = getErrorMessage(error, "Не удалось отправить отзыв.");
  }
};

watchEffect(() => {
  productLoadError.value = productError.value ? "Не удалось загрузить товар. Проверьте ссылку или попробуйте позже." : "";
});
</script>

<template>
  <div v-if="product" class="shell space-y-10">
    <section class="grid gap-8 xl:grid-cols-[1.05fr_0.95fr]">
      <div class="overflow-hidden rounded-[2rem] bg-white shadow-soft">
        <img :src="product.image_url" :alt="product.name" class="h-full min-h-[320px] w-full object-cover lg:min-h-[420px]" />
      </div>

      <div class="space-y-6">
        <div class="space-y-4">
          <div class="flex flex-wrap items-center gap-3">
            <span class="badge !bg-pine">{{ formatCategoryName(product.category.name) }}</span>
            <span
              v-if="product.discount_percent"
              class="rounded-full bg-clay/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-clay"
            >
              Скидка -{{ product.discount_percent }}%
            </span>
          </div>

          <div>
            <h1 class="font-display text-3xl font-bold text-ink sm:text-5xl">{{ product.name }}</h1>
            <div class="mt-3 flex flex-wrap items-center gap-4 text-sm text-slate-500">
              <p>
                Сейчас выбрано предложение магазина
                <NuxtLink :to="`/sellers/${product.seller.id}`" class="font-semibold text-pine hover:underline">
                  {{ product.seller.shop_name }}
                </NuxtLink>
              </p>
              <NuxtLink 
                v-if="auth.loggedIn && auth.user?.id !== product.seller.user_id" 
                :to="`/chat?seller_id=${product.seller.id}`" 
                class="rounded-full bg-sky-100 px-3 py-1 text-xs font-semibold text-ink hover:bg-sky-200 transition-colors"
              >
                💬 Написать продавцу
              </NuxtLink>
            </div>
          </div>
        </div>

        <div class="rounded-[1.8rem] bg-white p-6 shadow-soft">
          <div class="flex flex-wrap items-end justify-between gap-5">
            <div>
              <p class="text-3xl font-extrabold text-ink sm:text-4xl">{{ formatMoney(product.price) }}</p>
              <p v-if="product.old_price" class="mt-2 text-base text-slate-400 line-through">{{ formatMoney(product.old_price) }}</p>
            </div>
            <div class="grid gap-3 text-sm text-slate-500 sm:grid-cols-3">
              <div class="rounded-2xl bg-slate-50 px-4 py-3">
                <p class="text-xs uppercase tracking-[0.16em]">Рейтинг</p>
                <p class="mt-2 text-lg font-bold text-ink">{{ formatRating(product.average_rating) }}</p>
              </div>
              <div class="rounded-2xl bg-slate-50 px-4 py-3">
                <p class="text-xs uppercase tracking-[0.16em]">Отзывы</p>
                <p class="mt-2 text-lg font-bold text-ink">{{ product.reviews_count }}</p>
              </div>
              <div class="rounded-2xl bg-slate-50 px-4 py-3">
                <p class="text-xs uppercase tracking-[0.16em]">Остаток</p>
                <p class="mt-2 text-lg font-bold text-ink">{{ product.stock }}</p>
              </div>
            </div>
          </div>

          <div class="mt-6 flex flex-col gap-3 sm:flex-row">
            <button class="btn-primary flex-1" type="button" @click="addToCart">
              Добавить в корзину
            </button>
            <button class="btn-secondary flex-1" type="button" @click="toggleFavorite">
              {{ isFavorite ? "Убрать из избранного" : "Добавить в избранное" }}
            </button>
          </div>
        </div>

        <div class="panel p-6">
          <h2 class="section-title">Описание</h2>
          <p class="mt-4 text-base leading-8 text-slate-600">{{ product.description }}</p>

          <div class="mt-5 flex flex-wrap gap-2">
            <span
              v-for="tag in product.tags"
              :key="tag.id"
              class="rounded-full bg-mist px-3 py-1 text-sm font-semibold text-pine"
            >
              #{{ formatTagName(tag.name) }}
            </span>
          </div>
        </div>
      </div>
    </section>

    <SellerOffersPanel :offers="offers" :current-product-id="product.id" />

    <section class="grid gap-8 lg:grid-cols-[0.92fr_1.08fr]">
      <div class="panel p-6">
        <h2 class="section-title">Оставить отзыв</h2>
        <div class="mt-5 space-y-4">
          <div class="space-y-2">
            <label class="text-sm font-semibold text-ink">Оценка</label>
            <select v-model="reviewForm.rating" class="field">
              <option :value="5">5</option>
              <option :value="4">4</option>
              <option :value="3">3</option>
              <option :value="2">2</option>
              <option :value="1">1</option>
            </select>
          </div>
          <div class="space-y-2">
            <label class="text-sm font-semibold text-ink">Текст отзыва</label>
            <textarea v-model="reviewForm.text" rows="5" class="field" />
          </div>
          <p v-if="reviewError" class="text-sm text-rose-500">{{ reviewError }}</p>
          <p v-if="reviewSuccess" class="text-sm text-pine">{{ reviewSuccess }}</p>
          <button class="btn-primary w-full" type="button" @click="submitReview">Отправить отзыв</button>
        </div>
      </div>

      <div class="space-y-5">
        <div>
          <h2 class="section-title">Отзывы покупателей</h2>
          <p class="mt-2 text-sm text-slate-500">Посмотрите, что пишут о конкретном товаре перед покупкой.</p>
        </div>
        <ReviewList :reviews="reviews" />
      </div>
    </section>

    <RecommendationSection title="Похожие товары" subtitle="Похожие по категории, цене и тегам" :products="similarProducts" />
  </div>
  <div v-else class="shell">
    <div class="panel border border-rose-200 p-8 text-center text-sm text-rose-500">
      {{ productLoadError }}
    </div>
  </div>
</template>
