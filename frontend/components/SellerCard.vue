<script setup lang="ts">
import type { Seller } from "~/types";
import { useFormatters } from "~/composables/useFormatters";

defineProps<{
  seller: Seller;
}>();

const { formatRating } = useFormatters();
</script>

<template>
  <article class="relative overflow-hidden rounded-[1.6rem] border border-slate-100 bg-white p-5 shadow-soft">
    <div class="absolute inset-x-0 top-0 h-16 bg-gradient-to-r from-clay/10 via-transparent to-pine/10" />
    <div class="relative flex items-start gap-4">
      <img :src="seller.avatar" :alt="seller.shop_name" class="h-16 w-16 rounded-2xl border border-white object-cover shadow-soft" />
      <div class="min-w-0 flex-1">
        <NuxtLink :to="`/sellers/${seller.id}`" class="font-display text-xl font-bold text-ink">
          {{ seller.shop_name }}
        </NuxtLink>
        <p class="mt-2 line-clamp-3 text-sm text-slate-500">{{ seller.description }}</p>
      </div>
    </div>
    <div class="relative mt-5 grid grid-cols-2 gap-3 text-sm">
      <div class="rounded-2xl bg-slate-50 p-3">
        <p class="text-slate-500">Товаров</p>
        <p class="mt-1 font-bold text-ink">{{ seller.product_count || 0 }}</p>
      </div>
      <div class="rounded-2xl bg-slate-50 p-3">
        <p class="text-slate-500">Рейтинг</p>
        <p class="mt-1 font-bold text-ink">{{ formatRating(seller.average_rating) }}</p>
      </div>
    </div>
  </article>
</template>
