<script setup lang="ts">
import { useAuthStore } from "~/stores/auth";
import { useCartStore } from "~/stores/cart";

const auth = useAuthStore();
const cartStore = useCartStore();

const links = computed(() => {
  const base = [
    { label: "Каталог", to: "/catalog" },
    { label: "Корзина", to: "/cart" }
  ];

  if (auth.user?.role === "seller") {
    base.push({ label: "Продавец", to: "/seller" });
  }

  if (auth.loggedIn) {
    base.push({ label: "Кабинет", to: "/account" });
  }

  return base;
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
          class="pill-link"
        >
          {{ link.label }}
        </NuxtLink>
      </nav>

      <div class="flex items-center gap-3">
        <NuxtLink to="/cart" class="relative rounded-2xl border border-slate-200 bg-white/90 px-4 py-2 text-sm font-semibold shadow-soft">
          Корзина
          <span
            v-if="cartStore.count"
            class="absolute -right-2 -top-2 flex h-6 w-6 items-center justify-center rounded-full bg-clay text-xs text-white"
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
