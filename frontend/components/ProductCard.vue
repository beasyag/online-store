<script setup lang="ts">
import type { Product } from "~/types";
import { useFormatters } from "~/composables/useFormatters";
import { useAuthStore } from "~/stores/auth";
import { useCartStore } from "~/stores/cart";
import { useFavoritesStore } from "~/stores/favorites";

const props = defineProps<{
  product: Product;
}>();

const auth = useAuthStore();
const cartStore = useCartStore();
const favoritesStore = useFavoritesStore();
const { formatMoney, formatRating, formatCategoryName, formatTagName } = useFormatters();

const isFavorite = computed(() => favoritesStore.ids.has(props.product.id) || props.product.is_favorite);

const addToCart = async () => {
  if (!auth.loggedIn) {
    return navigateTo("/login");
  }
  await cartStore.addToCart(props.product.id, 1);
};

const toggleFavorite = async () => {
  if (!auth.loggedIn) {
    return navigateTo("/login");
  }
  await favoritesStore.toggleFavorite(props.product.id);
};
</script>

<template>
  <article class="group overflow-hidden rounded-[1.7rem] border border-white/80 bg-white/95 shadow-soft transition hover:-translate-y-0.5">
    <NuxtLink :to="`/products/${product.id}`" class="relative block aspect-[4/3] overflow-hidden bg-white">
      <img
        :src="product.image_url"
        :alt="product.name"
        class="h-full w-full object-cover transition duration-300 group-hover:scale-[1.03]"
      />
      <div class="absolute inset-x-0 bottom-0 h-28 bg-gradient-to-t from-slate-950/45 via-transparent to-transparent" />
      <div class="absolute left-4 top-4 flex flex-wrap gap-2">
        <span v-if="product.old_price" class="badge !bg-clay">
          Скидка {{ Math.round((1 - Number(product.price) / Number(product.old_price)) * 100) }}%
        </span>
        <span class="badge !bg-white/90 !text-ink">{{ formatCategoryName(product.category.name) }}</span>
      </div>
      <div class="absolute bottom-5 left-4 right-5">
        <p class="text-sm font-semibold text-white/75">{{ product.seller.shop_name }}</p>
        <p class="mt-1 line-clamp-2 text-lg font-bold text-white">{{ product.name }}</p>
      </div>
    </NuxtLink>

    <div class="space-y-4 p-5">
      <div class="flex items-start justify-between gap-3">
        <p class="line-clamp-3 text-sm leading-6 text-slate-500">{{ product.description }}</p>
        <button
          type="button"
          class="rounded-full border border-slate-200 px-3 py-2 text-xs font-semibold transition hover:border-clay hover:text-clay"
          @click.stop="toggleFavorite"
        >
          {{ isFavorite ? "Снять" : "В избр." }}
        </button>
      </div>

      <div class="flex items-end justify-between gap-3">
        <div>
          <p class="text-lg font-extrabold text-ink">{{ formatMoney(product.price) }}</p>
          <p v-if="product.old_price" class="text-sm text-slate-400 line-through">{{ formatMoney(product.old_price) }}</p>
        </div>
        <div class="text-right text-sm text-slate-500">
          <p>Рейтинг {{ formatRating(product.average_rating) }}</p>
          <p>{{ product.reviews_count }} отзывов</p>
        </div>
      </div>

      <div class="flex flex-wrap gap-2">
        <span
          v-for="tag in product.tags?.slice(0, 3)"
          :key="tag.id"
          class="rounded-full bg-mist px-3 py-1 text-xs font-semibold text-pine"
        >
          #{{ formatTagName(tag.name) }}
        </span>
      </div>

      <button class="btn-primary w-full" type="button" @click="addToCart">
        В корзину
      </button>
    </div>
  </article>
</template>
