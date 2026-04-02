<script setup lang="ts">
import type { Product } from "~/types";

defineProps<{
  products: Product[];
  emptyTitle?: string;
  emptyText?: string;
}>();
</script>

<template>
  <div v-if="products.length" class="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
    <ProductCard v-for="product in products" :key="product.id" :product="product" />
  </div>
  <div v-else class="panel p-8 text-center">
    <h3 class="font-display text-xl font-bold text-ink">{{ emptyTitle || "Товары не найдены" }}</h3>
    <p class="mt-2 text-sm text-slate-500">
      {{ emptyText || "Попробуйте изменить поисковый запрос или фильтры." }}
    </p>
  </div>
</template>
