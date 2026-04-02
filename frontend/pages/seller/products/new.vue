<script setup lang="ts">
import type { Category, Product, Tag } from "~/types";
import { useApiClient } from "~/composables/useApiClient";
import { usePaginatedResults } from "~/composables/usePaginatedResults";
import { useAuthStore } from "~/stores/auth";

const auth = useAuthStore();
const api = useApiClient();

await auth.bootstrap();

const { data: categoriesData } = await useAsyncData("seller-form-categories", () => api.get<Category[] | { results: Category[] }>("/categories/"));
const { data: tagsData } = await useAsyncData("seller-form-tags", () => api.get<Tag[] | { results: Tag[] }>("/tags/"));

const categories = computed(() => usePaginatedResults<Category>(categoriesData.value as any));
const tags = computed(() => usePaginatedResults<Tag>(tagsData.value as any));
const errorMessage = ref("");

const createProduct = async (payload: Record<string, unknown>) => {
  errorMessage.value = "";
  try {
    const body = {
      ...payload,
      old_price: payload.old_price || null
    };
    const product = await api.post<Product>("/products/", body);
    navigateTo(`/seller/products/${product.id}`);
  } catch (error: any) {
    errorMessage.value = error?.data?.detail || "Не удалось создать товар.";
  }
};
</script>

<template>
  <div class="shell space-y-8">
    <div>
      <span class="badge !bg-pine">Новый товар</span>
      <h1 class="section-title mt-3">Создать товар</h1>
    </div>

    <p v-if="errorMessage" class="panel border border-rose-200 p-5 text-sm text-rose-500">{{ errorMessage }}</p>

    <SellerProductForm :categories="categories" :tags="tags" submit-label="Создать товар" @submit="createProduct" />
  </div>
</template>
