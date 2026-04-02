<script setup lang="ts">
import { useAuthStore } from "~/stores/auth";
import { useFavoritesStore } from "~/stores/favorites";

const auth = useAuthStore();
const favoritesStore = useFavoritesStore();

await auth.bootstrap();
if (auth.loggedIn) {
  await favoritesStore.fetchFavorites();
}

const favoriteProducts = computed(() => favoritesStore.items.map((item) => item.product));
</script>

<template>
  <div class="shell space-y-8">
    <div>
      <span class="badge !bg-clay">Избранное</span>
      <h1 class="section-title mt-3">Сохраненные товары</h1>
    </div>

    <div v-if="!auth.loggedIn" class="panel p-8 text-center text-sm text-slate-500">
      Войдите, чтобы открыть избранное.
    </div>

    <ProductGrid
      v-else
      :products="favoriteProducts"
      empty-title="Пока нет избранных товаров"
      empty-text="Добавляйте товары в избранное с карточки товара."
    />
  </div>
</template>
