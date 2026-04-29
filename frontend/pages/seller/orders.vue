<script setup lang="ts">
import type { Order, PaginatedResponse } from "~/types";
import { useApiClient } from "~/composables/useApiClient";
import { usePaginatedResults } from "~/composables/usePaginatedResults";
import { useAuthStore } from "~/stores/auth";

const auth = useAuthStore();
const api = useApiClient();

await auth.bootstrap();

const { data: ordersData } = await useAsyncData("seller-orders", () =>
  auth.loggedIn ? api.get<PaginatedResponse<Order>>("/orders/seller/") : Promise.resolve(null)
);

const orders = computed(() => usePaginatedResults<Order>(ordersData.value));
</script>

<template>
  <div class="shell space-y-8">
    <div class="space-y-2">
      <span class="badge !bg-pine">Заказы продавца</span>
      <h1 class="section-title mt-3">Заказы с вашими товарами</h1>
    </div>

    <div v-if="!auth.loggedIn" class="panel p-8 text-center text-sm text-slate-500">
      Войдите, чтобы открыть заказы продавца.
    </div>

    <div v-else class="space-y-4">
      <OrderCard v-for="order in orders" :key="order.id" :order="order" seller-mode />
      <div v-if="!orders.length" class="panel p-8 text-center text-sm text-slate-500">
        Заказы появятся после первых покупок ваших товаров.
      </div>
    </div>
  </div>
</template>
