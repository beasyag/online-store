<script setup lang="ts">
import type { Order, PaginatedResponse } from "~/types";
import { useApiClient } from "~/composables/useApiClient";
import { usePaginatedResults } from "~/composables/usePaginatedResults";
import { useAuthStore } from "~/stores/auth";

const auth = useAuthStore();
const api = useApiClient();

await auth.bootstrap();

const { data: ordersData } = await useAsyncData("account-orders", () =>
  auth.loggedIn ? api.get<PaginatedResponse<Order>>("/orders/") : Promise.resolve(null)
);

const orders = computed(() => usePaginatedResults<Order>(ordersData.value));
</script>

<template>
  <div class="shell space-y-8">
    <div>
      <span class="badge">Заказы</span>
      <h1 class="section-title mt-3">История заказов</h1>
    </div>

    <div v-if="!auth.loggedIn" class="panel p-8 text-center text-sm text-slate-500">
      Войдите, чтобы увидеть свои заказы.
    </div>

    <div v-else class="space-y-4">
      <OrderCard v-for="order in orders" :key="order.id" :order="order" />
      <div v-if="!orders.length" class="panel p-8 text-center text-sm text-slate-500">
        Заказов пока нет. Добавьте товары в корзину и создайте первый заказ.
      </div>
    </div>
  </div>
</template>
