<script setup lang="ts">
import type { ChatRoom, PaginatedResponse, Order, SellerDashboardResponse } from "~/types";
import { useApiClient } from "~/composables/useApiClient";
import { useHeaderBadges } from "~/composables/useHeaderBadges";
import { useAuthStore } from "~/stores/auth";
import { useCartStore } from "~/stores/cart";
import { useFavoritesStore } from "~/stores/favorites";

const auth = useAuthStore();
const cartStore = useCartStore();
const favoritesStore = useFavoritesStore();
const api = useApiClient();
const { setBadge, getBadge } = useHeaderBadges();
let refreshTimer: ReturnType<typeof setInterval> | null = null;

const links = computed(() => {
  const base = [
    { label: "Каталог", to: "/catalog" },
    { label: "Корзина", to: "/cart" }
  ];

  if (auth.user?.role === "seller") {
    base.push({ label: "Продавец", to: "/seller" });
  }

  if (auth.loggedIn) {
    base.push({ label: "Сообщения", to: "/chat" });
    base.push({ label: "Кабинет", to: "/account" });
  }

  return base;
});

const syncCartBadge = () => {
  setBadge("/cart", cartStore.count);
};

const loadHeaderBadges = async () => {
  syncCartBadge();

  if (!auth.loggedIn) {
    setBadge("/chat", 0);
    setBadge("/account", 0);
    setBadge("/seller", 0);
    return;
  }

  await Promise.allSettled([
    api.get<ChatRoom[]>("/chat/rooms/list/").then((rooms) => {
      setBadge("/chat", rooms.reduce((total, room) => total + Number(room.unread_count || 0), 0));
    }),
    Promise.allSettled([
      favoritesStore.fetchFavorites(),
      api.get<PaginatedResponse<Order>>("/orders/")
    ]).then(([, ordersResult]) => {
      const ordersCount = ordersResult.status === "fulfilled" ? Number(ordersResult.value.count || 0) : 0;
      setBadge("/account", favoritesStore.items.length + ordersCount);
    }),
    auth.user?.role === "seller"
      ? api.get<SellerDashboardResponse>("/seller/dashboard/").then((dashboard) => {
          setBadge("/seller", Number(dashboard.orders_count || 0));
        })
      : Promise.resolve()
  ]);
};

const refreshHeaderBadges = () => {
  if (!process.client || document.hidden) {
    return;
  }
  void loadHeaderBadges();
};

const startBadgePolling = () => {
  if (!process.client || refreshTimer) {
    return;
  }
  refreshTimer = setInterval(refreshHeaderBadges, 5000);
};

const stopBadgePolling = () => {
  if (!refreshTimer) {
    return;
  }
  clearInterval(refreshTimer);
  refreshTimer = null;
};

const handleVisibilityChange = () => {
  if (document.hidden) {
    return;
  }
  refreshHeaderBadges();
};

watch(
  () => cartStore.count,
  () => {
    syncCartBadge();
  },
  { immediate: true }
);

watch(
  () => [auth.loggedIn, auth.user?.role] as const,
  () => {
    void loadHeaderBadges();
  },
  { immediate: true }
);

onMounted(() => {
  startBadgePolling();
  document.addEventListener("visibilitychange", handleVisibilityChange);
});

onUnmounted(() => {
  stopBadgePolling();
  document.removeEventListener("visibilitychange", handleVisibilityChange);
});
</script>

<template>
  <header class="sticky top-0 z-30 border-b border-white/50 bg-sand/70 backdrop-blur-xl">
    <div class="shell flex items-center justify-between gap-4 py-4">
      <NuxtLink to="/" class="flex items-center gap-3">
        <div class="flex h-12 w-12 items-center justify-center rounded-[1.25rem] bg-gradient-to-br from-ink via-slate-900 to-clay text-lg font-bold text-white shadow-soft">
          MK
        </div>
        <div>
          <p class="font-display text-lg font-bold">MarketFlow</p>
          <p class="muted">Маркетплейс с разными продавцами</p>
        </div>
      </NuxtLink>

      <nav class="hidden items-center gap-3 md:flex">
        <NuxtLink
          v-for="link in links"
          :key="link.to"
          :to="link.to"
          class="pill-link relative"
        >
          {{ link.label }}
          <span
            v-if="getBadge(link.to)"
            class="absolute -right-2 -top-2 flex h-6 min-w-6 items-center justify-center rounded-full bg-clay px-1 text-xs font-semibold text-white"
          >
            {{ getBadge(link.to) }}
          </span>
        </NuxtLink>
      </nav>

      <div class="flex items-center gap-3">
        <NuxtLink to="/cart" class="relative rounded-2xl border border-slate-200 bg-white/90 px-4 py-2 text-sm font-semibold shadow-soft md:hidden">
          Корзина
          <span
            v-if="cartStore.count"
            class="absolute -right-2 -top-2 flex h-6 min-w-6 items-center justify-center rounded-full bg-clay px-1 text-xs font-semibold text-white"
          >
            {{ cartStore.count }}
          </span>
        </NuxtLink>

        <template v-if="auth.loggedIn">
          <NuxtLink to="/account" class="hidden rounded-2xl border border-slate-200 bg-white/90 px-4 py-2 text-sm font-semibold shadow-soft sm:inline-flex">
            {{ auth.fullName || "Профиль" }}
          </NuxtLink>
          <button class="btn-primary !px-4 !py-2" type="button" @click="auth.logout()">
            Выйти
          </button>
        </template>
        <template v-else>
          <NuxtLink to="/login" class="btn-secondary !px-4 !py-2">Войти</NuxtLink>
          <NuxtLink to="/register" class="btn-primary !px-4 !py-2">Регистрация</NuxtLink>
        </template>
      </div>
    </div>
  </header>
</template>
