<script setup lang="ts">
import type { Product } from "~/types";

defineProps<{
  title: string;
  subtitle?: string;
  products: Product[];
  reasons?: string[];
}>();
</script>

<template>
  <section class="section-block space-y-5">
    <div class="flex items-end justify-between gap-4">
      <div>
        <p class="badge !bg-pine">{{ subtitle || "Подборка для вас" }}</p>
        <h2 class="section-title mt-3">{{ title }}</h2>
      </div>
      <NuxtLink to="/catalog" class="hidden text-sm font-semibold text-slate-500 hover:text-ink sm:inline-flex">
        В каталог
      </NuxtLink>
    </div>
    <div v-if="reasons?.length" class="grid gap-3 rounded-[1.8rem] border border-white/70 bg-white/85 p-5 sm:grid-cols-3">
      <div v-for="reason in reasons" :key="reason" class="rounded-2xl bg-mist px-4 py-3 text-sm font-semibold text-pine">
        {{ reason }}
      </div>
    </div>
    <ProductGrid :products="products" empty-title="Пока нечего показать" empty-text="Этот блок заполнится после генерации данных." />
  </section>
</template>
