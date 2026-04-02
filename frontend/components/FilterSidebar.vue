<script setup lang="ts">
import type { Category } from "~/types";
import { useFormatters } from "~/composables/useFormatters";

interface CatalogFilters {
  category: string;
  minPrice: string;
  maxPrice: string;
  ordering: string;
}

const props = defineProps<{
  categories: Category[];
  modelValue: CatalogFilters;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: CatalogFilters];
}>();

const filters = reactive<CatalogFilters>({ ...props.modelValue });
const { formatCategoryName } = useFormatters();

watch(
  () => props.modelValue,
  (value) => Object.assign(filters, value),
  { deep: true }
);

watch(
  filters,
  () => emit("update:modelValue", { ...filters }),
  { deep: true }
);
</script>

<template>
  <aside class="panel space-y-4 p-5 lg:sticky lg:top-24">
    <div class="space-y-2">
      <label class="text-sm font-semibold text-ink" for="category">Категория</label>
      <select id="category" v-model="filters.category" class="field">
        <option value="">Все категории</option>
        <option v-for="category in categories" :key="category.id" :value="category.slug">
          {{ formatCategoryName(category.name) }}
        </option>
      </select>
    </div>

    <div class="grid grid-cols-2 gap-3">
      <div class="space-y-2">
        <label class="text-sm font-semibold text-ink" for="min-price">Цена от</label>
        <input id="min-price" v-model="filters.minPrice" type="number" min="0" class="field" />
      </div>
      <div class="space-y-2">
        <label class="text-sm font-semibold text-ink" for="max-price">Цена до</label>
        <input id="max-price" v-model="filters.maxPrice" type="number" min="0" class="field" />
      </div>
    </div>

    <div class="space-y-2">
      <label class="text-sm font-semibold text-ink" for="ordering">Сортировка</label>
      <select id="ordering" v-model="filters.ordering" class="field">
        <option value="popular">Сначала популярные</option>
        <option value="new">Сначала новинки</option>
        <option value="rating">Сначала с высоким рейтингом</option>
        <option value="price_asc">Цена: по возрастанию</option>
        <option value="price_desc">Цена: по убыванию</option>
      </select>
    </div>
  </aside>
</template>
