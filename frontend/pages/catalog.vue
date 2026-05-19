<script setup lang="ts">
import type { PaginatedResponse, Product } from "~/types";
import { useApiClient } from "~/composables/useApiClient";
import { usePaginatedResults } from "~/composables/usePaginatedResults";

const api = useApiClient();

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

const { data: catalogData, pending: catalogPending, error: catalogError, refresh: refreshCatalog } = await useAsyncData(
  "catalog-page",
  () => api.get<PaginatedResponse<Product>>(`/products/?${catalogQuery.value}`),
  { watch: [catalogQuery] }
);

const products = computed(() => usePaginatedResults<Product>(catalogData.value));
const catalogErrorMessage = computed(() =>
  catalogError.value ? "Не удалось загрузить каталог. Обновите страницу или попробуйте позже." : ""
);

const runSearch = () => refreshCatalog();

useHead({
  title: "Каталог | MarketFlow"
});
</script>

<template>
  <div class="shell space-y-8">
    <section class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <p class="badge !bg-clay">Каталог</p>
        <h1 class="section-title mt-3">Все товары витрины</h1>
        <p class="mt-2 max-w-2xl text-sm text-slate-500">
          Отдельная страница каталога с поиском по витрине, где каждая карточка показывает один товар без дублей по offer group.
        </p>
      </div>
      <p class="text-sm text-slate-500">{{ catalogData?.count || products.length }} товаров</p>
    </section>

    <SearchBar v-model="search" @submit="runSearch" />

    <div v-if="catalogPending" class="panel p-8 text-center text-sm text-slate-500">
      Загружаем товары...
    </div>
    <div v-else-if="catalogErrorMessage" class="panel border border-rose-200 p-8 text-center text-sm text-rose-500">
      {{ catalogErrorMessage }}
    </div>
    <div v-else class="section-block">
      <ProductGrid :products="products" />
    </div>
  </div>
</template>
