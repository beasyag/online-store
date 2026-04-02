<script setup lang="ts">
import type { Product } from "~/types";

defineProps<{
  title: string;
  subtitle?: string;
  products: Product[];
}>();
</script>

<template>
  <section class="section-block space-y-5">
    <div class="flex items-end justify-between gap-4">
      <div>
        <p class="badge !bg-pine">{{ subtitle || "Подборка для вас" }}</p>
        <h2 class="section-title mt-3">{{ title }}</h2>
      </div>
      <NuxtLink to="/" class="hidden text-sm font-semibold text-slate-500 hover:text-ink sm:inline-flex">
        В каталог
      </NuxtLink>
    </div>
    <ProductGrid :products="products" empty-title="Пока нечего показать" empty-text="Этот блок заполнится после генерации данных." />
  </section>
</template>
