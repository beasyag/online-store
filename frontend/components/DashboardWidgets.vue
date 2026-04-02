<script setup lang="ts">
import { useFormatters } from "~/composables/useFormatters";

defineProps<{
  metrics: {
    product_count: number;
    orders_count: number;
    sales_count: number;
    total_sales: string;
  };
}>();

const { formatMoney } = useFormatters();
</script>

<template>
  <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
    <div class="panel p-5">
      <p class="text-sm text-slate-500">Товары</p>
      <p class="mt-2 font-display text-3xl font-bold">{{ metrics.product_count }}</p>
    </div>
    <div class="panel p-5">
      <p class="text-sm text-slate-500">Заказы</p>
      <p class="mt-2 font-display text-3xl font-bold">{{ metrics.orders_count }}</p>
    </div>
    <div class="panel p-5">
      <p class="text-sm text-slate-500">Продано</p>
      <p class="mt-2 font-display text-3xl font-bold">{{ metrics.sales_count }}</p>
    </div>
    <div class="panel p-5">
      <p class="text-sm text-slate-500">Выручка</p>
      <p class="mt-2 font-display text-3xl font-bold">{{ formatMoney(metrics.total_sales) }}</p>
    </div>
  </div>
</template>
