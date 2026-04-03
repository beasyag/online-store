<script setup lang="ts">
import type { Order } from "~/types";
import { useFormatters } from "~/composables/useFormatters";

const props = defineProps<{
  order: Order;
  sellerMode?: boolean;
}>();

const { formatDate, formatMoney, formatOrderStatus, formatOrderStatusHint } = useFormatters();

const statusClass = computed(() => {
  const classes: Record<string, string> = {
    pending: "border-amber-200 bg-amber-50 text-amber-700",
    paid: "border-sky-200 bg-sky-50 text-sky-700",
    processing: "border-indigo-200 bg-indigo-50 text-indigo-700",
    shipped: "border-violet-200 bg-violet-50 text-violet-700",
    completed: "border-emerald-200 bg-emerald-50 text-emerald-700",
    canceled: "border-rose-200 bg-rose-50 text-rose-700"
  };
  return classes[props.order.status] || "border-pine/20 bg-mist text-pine";
});
</script>

<template>
  <article class="panel p-5">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p class="text-sm font-semibold uppercase tracking-[0.16em] text-slate-500">Заказ #{{ order.id }}</p>
        <p class="mt-2 text-sm text-slate-500">{{ formatDate(order.created_at) }}</p>
      </div>
      <div class="flex flex-wrap items-center gap-3">
        <span class="rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em]" :class="statusClass">
          {{ formatOrderStatus(order.status) }}
        </span>
        <span class="text-lg font-bold text-ink">
          {{ formatMoney(order.seller_total || order.total_amount) }}
        </span>
      </div>
    </div>
    <p class="mt-3 text-sm text-slate-500">{{ formatOrderStatusHint(order.status) }}</p>

    <div class="mt-5 space-y-3">
      <div
        v-for="item in order.items"
        :key="item.id"
        class="flex flex-col gap-2 rounded-2xl border border-slate-100 bg-slate-50 p-4 sm:flex-row sm:items-center sm:justify-between"
      >
        <div>
          <p class="font-semibold text-ink">{{ item.product.name }}</p>
          <p class="text-sm text-slate-500">{{ item.seller.shop_name }}</p>
        </div>
        <div class="text-sm text-slate-500">
          <p>{{ item.quantity }} x {{ formatMoney(item.price_at_purchase) }}</p>
          <p class="font-semibold text-ink">{{ formatMoney(item.subtotal) }}</p>
        </div>
      </div>
    </div>
  </article>
</template>
