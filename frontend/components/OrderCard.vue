<script setup lang="ts">
import type { Order } from "~/types";
import { useFormatters } from "~/composables/useFormatters";

defineProps<{
  order: Order;
  sellerMode?: boolean;
}>();

const { formatDate, formatMoney, formatOrderStatus } = useFormatters();
</script>

<template>
  <article class="panel p-5">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p class="text-sm font-semibold uppercase tracking-[0.16em] text-slate-500">Заказ #{{ order.id }}</p>
        <p class="mt-2 text-sm text-slate-500">{{ formatDate(order.created_at) }}</p>
      </div>
      <div class="flex flex-wrap items-center gap-3">
        <span class="rounded-full bg-mist px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em] text-pine">
          {{ formatOrderStatus(order.status) }}
        </span>
        <span class="text-lg font-bold text-ink">
          {{ formatMoney(order.seller_total || order.total_amount) }}
        </span>
      </div>
    </div>

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
