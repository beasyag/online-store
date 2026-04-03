<script setup lang="ts">
import { useApiError } from "~/composables/useApiError";
import { useAuthStore } from "~/stores/auth";
import { useFavoritesStore } from "~/stores/favorites";

const auth = useAuthStore();
const favoritesStore = useFavoritesStore();
const { getErrorMessage } = useApiError();
const pageError = ref("");

await auth.bootstrap();
if (auth.loggedIn) {
  try {
    await favoritesStore.fetchFavorites();
  } catch (error: any) {
    pageError.value = getErrorMessage(error, "Не удалось загрузить избранное.");
  }
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

    <div v-else class="space-y-4">
      <div v-if="pageError" class="panel border border-rose-200 p-5 text-sm text-rose-500">
        {{ pageError }}
      </div>
      <ProductGrid
        :products="favoriteProducts"
        empty-title="Пока нет избранных товаров"
        empty-text="Добавляйте товары в избранное с карточки товара."
      />
    </div>
  </div>
</template>
