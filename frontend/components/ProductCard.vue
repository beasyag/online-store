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
const productBadges = computed(() => {
  const badges: Array<{ label: string; className: string }> = [];

  if (props.product.old_price) {
    badges.push({
      label: `Скидка ${Math.round((1 - Number(props.product.price) / Number(props.product.old_price)) * 100)}%`,
      className: "badge !bg-clay"
    });
  }

  const createdAt = props.product.created_at ? new Date(props.product.created_at).getTime() : 0;
  const daysSinceCreate = createdAt ? (Date.now() - createdAt) / (1000 * 60 * 60 * 24) : Number.POSITIVE_INFINITY;
  if (daysSinceCreate <= 14) {
    badges.push({
      label: "Новинка",
      className: "badge !bg-pine"
    });
  }

  if (props.product.purchases_count >= 20 || props.product.views_count >= 100) {
    badges.push({
      label: "Популярное",
      className: "badge !bg-white/90 !text-ink"
    });
  }

  return badges.slice(0, 2);
});

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
  <article class="group overflow-hidden rounded-[1.4rem] border border-white/80 bg-white/95 shadow-soft transition hover:-translate-y-0.5 sm:rounded-[1.7rem]">
    <NuxtLink :to="`/products/${product.id}`" class="relative block aspect-[4/3] overflow-hidden bg-white">
      <img
          :src="product.image_url"
          :alt="product.name"
          class="h-full w-full object-cover transition duration-300 group-hover:scale-[1.03]"
      />
      <div class="absolute inset-x-0 bottom-0 h-28 bg-gradient-to-t from-slate-950/45 via-transparent to-transparent" />
      <div class="absolute left-3 top-3 flex flex-wrap gap-2 sm:left-4 sm:top-4">
        <span v-for="badge in productBadges" :key="badge.label" :class="badge.className">
          {{ badge.label }}
        </span>
        <span v-if="!productBadges.length" class="badge !bg-white/90 !text-ink">{{ formatCategoryName(product.category.name) }}</span>
      </div>
      <div class="absolute bottom-4 left-3 right-4 sm:bottom-5 sm:left-4 sm:right-5">
        <p class="text-xs font-semibold text-white/75 sm:text-sm">{{ product.seller.shop_name }}</p>
        <p class="mt-1 line-clamp-2 text-base font-bold text-white sm:text-lg">{{ product.name }}</p>
      </div>
    </NuxtLink>

    <div class="space-y-4 p-4 sm:p-5">
      <div class="flex items-start justify-between gap-3">
        <p v-if="product.description" class="line-clamp-3 text-sm leading-5 text-slate-500 sm:leading-6">{{ product.description }}</p>
        <button
            type="button"
            class="rounded-full border border-slate-200 px-3 py-2 text-xs font-semibold transition hover:border-clay hover:text-clay"
            :class="{ 'ml-auto': !product.description }"
            @click.stop="toggleFavorite"
        >
          {{ isFavorite ? "Снять" : "В избр." }}
        </button>
      </div>

      <div class="flex items-end justify-between gap-3">
        <div>
          <p class="text-base font-extrabold text-ink sm:text-lg">{{ formatMoney(product.price) }}</p>
          <p v-if="product.old_price" class="text-sm text-slate-400 line-through">{{ formatMoney(product.old_price) }}</p>
        </div>
        <div class="text-right text-xs text-slate-500 sm:text-sm">
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
