<script setup lang="ts">
import type { PaginatedResponse, Product, RecommendationResponse } from "~/types";
import { useApiClient } from "~/composables/useApiClient";
import { usePaginatedResults } from "~/composables/usePaginatedResults";
import { useAuthStore } from "~/stores/auth";

const api = useApiClient();
const auth = useAuthStore();

const search = ref("");

const buildQuery = (params: Record<string, string | undefined>) => {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value) {
      query.set(key, value);
    }
  });
  return query.toString();
};

const catalogQuery = computed(() =>
  buildQuery({
    q: search.value || undefined,
    ordering: search.value ? undefined : "popular"
  })
);

const { data: dealsData } = await useAsyncData("deals-products", () => api.get<PaginatedResponse<Product>>("/products/deals/"));
const { data: catalogData, pending: catalogPending, error: catalogError, refresh: refreshCatalog } = await useAsyncData(
  "catalog",
  () => api.get<PaginatedResponse<Product>>(`/products/?${catalogQuery.value}`),
  { watch: [catalogQuery] }
);
const { data: popularData } = await useAsyncData("popular-products", () => api.get<PaginatedResponse<Product>>("/products/popular/"));
const { data: newData } = await useAsyncData("new-products", () => api.get<PaginatedResponse<Product>>("/products/new/"));
const { data: recommendationsData, refresh: refreshRecommendations } = await useAsyncData(
  "recommendations",
  () => api.get<RecommendationResponse>("/recommendations/"),
  { watch: [computed(() => auth.loggedIn)] }
);

const dealProducts = computed(() => usePaginatedResults<Product>(dealsData.value));
const products = computed(() => usePaginatedResults<Product>(catalogData.value));
const popularProducts = computed(() => usePaginatedResults<Product>(popularData.value));
const newProducts = computed(() => usePaginatedResults<Product>(newData.value));
const catalogErrorMessage = computed(() =>
  catalogError.value ? "Не удалось загрузить каталог. Обновите страницу или попробуйте позже." : ""
);
const recommendationReasons = computed(() => {
  if (recommendationsData.value?.strategy === "personalized") {
    return [
      "Похожие категории из просмотренных товаров",
      "Сигналы из корзины, избранного и покупок",
      "Усиление популярных и высоко оценённых позиций"
    ];
  }

  return [
    "Подборка по текущей популярности",
    "Учитываются просмотры, покупки и рейтинг",
    "Хороший старт для нового или анонимного пользователя"
  ];
});

watch(
  () => auth.loggedIn,
  () => refreshRecommendations()
);

const runSearch = () => refreshCatalog();
</script>

<template>
  <div class="shell space-y-10">
    <PromoSlider :products="dealProducts" />

    <SearchBar v-model="search" @submit="runSearch" />

    <section id="catalog" class="space-y-6">
      <div class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p class="badge !bg-clay">Каталог</p>
          <h2 class="section-title mt-3">Популярные и реальные товары</h2>
          <p class="mt-2 max-w-2xl text-sm text-slate-500">
            Смартфоны, игрушки, одежда, книги, товары для дома и другие позиции с несколькими продавцами внутри карточки товара.
          </p>
        </div>
        <p class="text-sm text-slate-500">{{ catalogData?.count || products.length }} товаров</p>
      </div>

      <div v-if="catalogPending" class="panel p-8 text-center text-sm text-slate-500">
        Загружаем товары...
      </div>
      <div v-else-if="catalogErrorMessage" class="panel border border-rose-200 p-8 text-center text-sm text-rose-500">
        {{ catalogErrorMessage }}
      </div>
      <div v-else class="section-block">
        <ProductGrid :products="products" />
      </div>
    </section>

    <RecommendationSection
      title="Рекомендуем вам"
      :subtitle="recommendationsData?.strategy === 'personalized' ? 'На основе просмотров, корзины и покупок' : 'Популярные товары для новых посетителей'"
      :products="recommendationsData?.results || []"
      :reasons="recommendationReasons"
    />

    <RecommendationSection title="Популярное" subtitle="Товары, которые сейчас смотрят и покупают" :products="popularProducts" />

    <RecommendationSection title="Новинки" subtitle="Недавние поступления в каталог" :products="newProducts" />
  </div>
</template>
