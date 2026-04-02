<script setup lang="ts">
import type { ProductOffer } from "~/types";
import { useFormatters } from "~/composables/useFormatters";

const props = defineProps<{
  offers: ProductOffer[];
  currentProductId: number;
}>();

const { formatMoney, formatRating } = useFormatters();

const sortedOffers = computed(() =>
  [...props.offers].sort((left, right) => {
    if (left.id === props.currentProductId) {
      return -1;
    }
    if (right.id === props.currentProductId) {
      return 1;
    }
    return Number(left.price) - Number(right.price);
  })
);

const openOffer = async (offerId: number) => {
  if (offerId === props.currentProductId) {
    return;
  }
  await navigateTo(`/products/${offerId}`);
};
</script>

<template>
  <section v-if="offers.length" class="panel space-y-5 p-6">
    <div class="flex items-start justify-between gap-4">
      <div>
        <span class="badge !bg-clay">Продавцы</span>
        <h2 class="section-title mt-3">Выберите предложение</h2>
        <p class="mt-2 text-sm text-slate-500">Один и тот же товар доступен у нескольких продавцов. Можно выбрать лучшую цену, рейтинг и остаток.</p>
      </div>
      <div class="rounded-2xl bg-slate-100 px-4 py-3 text-right">
        <p class="text-xs uppercase tracking-[0.16em] text-slate-500">Всего</p>
        <p class="mt-1 text-xl font-bold text-ink">{{ offers.length }}</p>
      </div>
    </div>

    <div class="space-y-3">
      <button
        v-for="offer in sortedOffers"
        :key="offer.id"
        type="button"
        class="flex w-full flex-col gap-4 rounded-[1.6rem] border p-4 text-left transition hover:border-clay/40 hover:bg-slate-50 sm:flex-row sm:items-center sm:justify-between"
        :class="offer.id === currentProductId ? 'border-clay bg-clay/5' : 'border-slate-200 bg-white'"
        @click="openOffer(offer.id)"
      >
        <div class="flex items-center gap-4">
          <img :src="offer.seller.avatar" :alt="offer.seller.shop_name" class="h-14 w-14 rounded-2xl object-cover" />
          <div>
            <p class="font-semibold text-ink">{{ offer.seller.shop_name }}</p>
            <p class="mt-1 text-sm text-slate-500">
              Рейтинг {{ formatRating(offer.average_rating) }} • {{ offer.reviews_count }} отзывов
            </p>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-4 sm:justify-end">
          <div class="text-sm text-slate-500">
            <p>Остаток: {{ offer.stock }}</p>
            <p v-if="offer.discount_percent" class="text-clay">Скидка -{{ offer.discount_percent }}%</p>
          </div>
          <div class="text-right">
            <p class="text-lg font-bold text-ink">{{ formatMoney(offer.price) }}</p>
            <p v-if="offer.old_price" class="text-sm text-slate-400 line-through">{{ formatMoney(offer.old_price) }}</p>
          </div>
          <span
            class="inline-flex rounded-2xl px-4 py-3 text-sm font-semibold"
            :class="offer.id === currentProductId ? 'bg-ink text-white' : 'bg-slate-100 text-ink'"
          >
            {{ offer.id === currentProductId ? 'Выбрано' : 'Выбрать' }}
          </span>
        </div>
      </button>
    </div>
  </section>
</template>
