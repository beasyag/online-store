<script setup lang="ts">
import type { PaginatedResponse, Product, Seller } from "~/types";
import { useApiClient } from "~/composables/useApiClient";
import { useFormatters } from "~/composables/useFormatters";
import { usePaginatedResults } from "~/composables/usePaginatedResults";

const route = useRoute();
const api = useApiClient();
const { formatRating } = useFormatters();

const sellerId = computed(() => Number(route.params.id));

const { data: seller } = await useAsyncData(
  `seller-${sellerId.value}`,
  () => api.get<Seller>(`/sellers/${sellerId.value}/`),
  { watch: [sellerId] }
);
const { data: sellerProductsData } = await useAsyncData(
  `seller-products-${sellerId.value}`,
  () => api.get<PaginatedResponse<Product>>(`/sellers/${sellerId.value}/products/`),
  { watch: [sellerId] }
);

const sellerProducts = computed(() => usePaginatedResults<Product>(sellerProductsData.value));
</script>

<template>
  <div v-if="seller" class="shell space-y-8">
    <section class="panel p-8">
      <div class="flex flex-col gap-6 md:flex-row md:items-center">
        <img :src="seller.avatar" :alt="seller.shop_name" class="h-24 w-24 rounded-3xl object-cover" />
        <div class="space-y-3">
          <span class="badge !bg-pine">Профиль продавца</span>
          <h1 class="font-display text-4xl font-bold text-ink">{{ seller.shop_name }}</h1>
          <p class="max-w-3xl text-base leading-7 text-slate-600">{{ seller.description }}</p>
          <div class="flex flex-wrap gap-4 text-sm text-slate-500">
            <span>{{ seller.product_count || sellerProducts.length }} активных товаров</span>
            <span>Рейтинг {{ formatRating(seller.average_rating) }}</span>
          </div>
        </div>
      </div>
    </section>

    <section class="space-y-5">
      <div>
        <h2 class="section-title">Товары продавца</h2>
        <p class="mt-2 text-sm text-slate-500">Текущие позиции, доступные в этом магазине.</p>
      </div>
      <ProductGrid :products="sellerProducts" empty-title="У продавца пока нет активных товаров" />
    </section>
  </div>
</template>
