<template>
  <div class="min-h-screen">
    <AppHeader />
    <div class="shell mt-4 space-y-3" v-if="notifications.items.length">
      <div
        v-for="item in notifications.items"
        :key="item.id"
        class="flex items-start justify-between gap-4 rounded-2xl border px-4 py-3 text-sm shadow-soft"
        :class="
          item.tone === 'error'
            ? 'border-rose-200 bg-rose-50 text-rose-700'
            : 'border-pine/20 bg-pine/10 text-pine'
        "
      >
        <p>{{ item.message }}</p>
        <button type="button" class="font-semibold" @click="notifications.remove(item.id)">Закрыть</button>
      </div>
    </div>
    <main class="pb-16 pt-6 sm:pb-20 sm:pt-8">
      <slot />
    </main>
    <footer class="border-t border-white/60 py-8">
      <div class="shell flex flex-col gap-2 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between">
        <p>MarketFlow MVP на Nuxt 3 и Django REST Framework.</p>
        <p>Персональные рекомендации, multi-vendor заказы и кабинет продавца.</p>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { useNotificationsStore } from "~/stores/notifications";

const notifications = useNotificationsStore();
</script>
