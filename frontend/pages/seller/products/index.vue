<script setup lang="ts">
import type { PaginatedResponse, Product } from "~/types";
import { useApiClient } from "~/composables/useApiClient";
import { useFormatters } from "~/composables/useFormatters";
import { usePaginatedResults } from "~/composables/usePaginatedResults";
import { useAuthStore } from "~/stores/auth";

const auth = useAuthStore();
const api = useApiClient();
const { formatMoney, formatCategoryName } = useFormatters();

await auth.bootstrap();

const { data: productsData, refresh: refreshProducts } = await useAsyncData("seller-products", () =>
  auth.loggedIn ? api.get<PaginatedResponse<Product>>("/products/?mine=1&ordering=new") : Promise.resolve(null)
);

const products = computed(() => usePaginatedResults<Product>(productsData.value));

const removeProduct = async (productId: number) => {
  await api.delete(`/products/${productId}/`);
  await refreshProducts();
};
</script>

<template>
  <div class="shell space-y-8">
    <section class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <span class="badge !bg-pine">Управление каталогом</span>
        <h1 class="section-title mt-3">Мои товары</h1>
      </div>
      <NuxtLink to="/seller/products/new" class="btn-primary">Добавить товар</NuxtLink>
    </section>

    <div class="grid gap-4">
      <article v-for="product in products" :key="product.id" class="panel p-5">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-center">
          <img :src="product.image_url" :alt="product.name" class="h-28 w-full rounded-2xl object-cover lg:w-40" />
          <div class="min-w-0 flex-1">
            <p class="font-display text-2xl font-bold text-ink">{{ product.name }}</p>
            <p class="mt-2 text-sm text-slate-500">{{ formatCategoryName(product.category.name) }} • Остаток: {{ product.stock }}</p>
            <p class="mt-3 text-sm font-semibold text-ink">{{ formatMoney(product.price) }}</p>
          </div>
          <div class="flex flex-wrap gap-3">
            <NuxtLink :to="`/seller/products/${product.id}`" class="btn-secondary">Редактировать</NuxtLink>
            <button class="rounded-2xl px-4 py-3 text-sm font-semibold text-rose-500" type="button" @click="removeProduct(product.id)">
              Удалить
            </button>
          </div>
        </div>
      </article>

      <div v-if="!products.length" class="panel p-8 text-center text-sm text-slate-500">
        Товаров пока нет. Добавьте первую позицию в каталог.
      </div>
    </div>
  </div>
</template>
