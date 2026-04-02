<script setup lang="ts">
import type { Category, Product, Tag } from "~/types";
import { useApiClient } from "~/composables/useApiClient";
import { usePaginatedResults } from "~/composables/usePaginatedResults";

const route = useRoute();
const api = useApiClient();

const productId = computed(() => Number(route.params.id));

const { data: productData } = await useAsyncData(
  `seller-product-${productId.value}`,
  () => api.get<Product>(`/products/${productId.value}/`),
  { watch: [productId] }
);
const { data: categoriesData } = await useAsyncData("seller-edit-categories", () => api.get<Category[] | { results: Category[] }>("/categories/"));
const { data: tagsData } = await useAsyncData("seller-edit-tags", () => api.get<Tag[] | { results: Tag[] }>("/tags/"));

const product = computed(() => productData.value);
const categories = computed(() => usePaginatedResults<Category>(categoriesData.value as any));
const tags = computed(() => usePaginatedResults<Tag>(tagsData.value as any));
const errorMessage = ref("");
const successMessage = ref("");

const updateProduct = async (payload: Record<string, unknown>) => {
  if (!product.value) {
    return;
  }
  errorMessage.value = "";
  successMessage.value = "";
  try {
    await api.put<Product>(`/products/${product.value.id}/`, {
      ...payload,
      old_price: payload.old_price || null
    });
    successMessage.value = "Товар успешно обновлен.";
  } catch (error: any) {
    errorMessage.value = error?.data?.detail || "Не удалось обновить товар.";
  }
};
</script>

<template>
  <div v-if="product" class="shell space-y-8">
    <div>
      <span class="badge !bg-pine">Редактирование товара</span>
      <h1 class="section-title mt-3">{{ product.name }}</h1>
    </div>

    <p v-if="errorMessage" class="panel border border-rose-200 p-5 text-sm text-rose-500">{{ errorMessage }}</p>
    <p v-if="successMessage" class="panel border border-pine/20 p-5 text-sm text-pine">{{ successMessage }}</p>

    <SellerProductForm
      :categories="categories"
      :tags="tags"
      :initial-value="{ ...product, category_id: product.category.id, tag_ids: product.tags.map((tag) => tag.id) }"
      submit-label="Сохранить изменения"
      @submit="updateProduct"
    />
  </div>
</template>
