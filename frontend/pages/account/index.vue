<script setup lang="ts">
import type { Order, PaginatedResponse } from "~/types";
import { useApiClient } from "~/composables/useApiClient";
import { usePaginatedResults } from "~/composables/usePaginatedResults";
import { useAuthStore } from "~/stores/auth";
import { useFavoritesStore } from "~/stores/favorites";

const auth = useAuthStore();
const favoritesStore = useFavoritesStore();
const api = useApiClient();

await auth.bootstrap();

const { data: ordersData } = await useAsyncData("account-orders-preview", () =>
  auth.loggedIn ? api.get<PaginatedResponse<Order>>("/orders/") : Promise.resolve(null)
);

if (auth.loggedIn && !favoritesStore.items.length) {
  await favoritesStore.fetchFavorites();
}

const orders = computed(() => usePaginatedResults<Order>(ordersData.value));
</script>

<template>
  <div class="shell space-y-8">
    <section class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <span class="badge">Кабинет</span>
        <h1 class="section-title mt-3">Кабинет покупателя</h1>
      </div>
      <div class="grid gap-3 sm:flex sm:flex-wrap">
        <NuxtLink to="/account/orders" class="btn-secondary w-full sm:w-auto">Заказы</NuxtLink>
        <NuxtLink to="/account/favorites" class="btn-primary w-full sm:w-auto">Избранное</NuxtLink>
      </div>
    </section>

    <div v-if="!auth.loggedIn" class="panel p-8 text-center text-sm text-slate-500">
      Войдите, чтобы открыть профиль, историю заказов и избранное.
    </div>

    <template v-else>
      <section class="grid gap-4 sm:grid-cols-3">
        <div class="panel p-4 sm:p-5">
          <p class="text-sm text-slate-500">Профиль</p>
          <p class="mt-2 break-words font-display text-xl font-bold text-ink sm:text-2xl">{{ auth.fullName || auth.user?.username }}</p>
          <p class="mt-1 text-sm text-slate-500">{{ auth.user?.email }}</p>
        </div>
        <div class="panel p-4 sm:p-5">
          <p class="text-sm text-slate-500">Заказы</p>
          <p class="mt-2 font-display text-2xl font-bold text-ink">{{ orders.length }}</p>
        </div>
        <div class="panel p-4 sm:p-5">
          <p class="text-sm text-slate-500">Избранное</p>
          <p class="mt-2 font-display text-2xl font-bold text-ink">{{ favoritesStore.items.length }}</p>
        </div>
      </section>

      <section class="space-y-5">
        <div>
          <h2 class="section-title">Последние заказы</h2>
          <p class="mt-2 text-sm text-slate-500">Последние multi-vendor заказы по текущему аккаунту.</p>
        </div>
        <OrderCard v-for="order in orders.slice(0, 3)" :key="order.id" :order="order" />
      </section>
    </template>
  </div>
</template>
