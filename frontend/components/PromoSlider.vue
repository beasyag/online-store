<script setup lang="ts">
import type { Product } from "~/types";
import { useFormatters } from "~/composables/useFormatters";

const props = defineProps<{
  products: Product[];
}>();

const { formatMoney, formatCategoryName } = useFormatters();
const activeIndex = ref(0);
let timer: ReturnType<typeof setInterval> | null = null;

const slides = computed(() => props.products.filter((product) => product.old_price && (product.discount_percent || 0) > 0).slice(0, 6));
const activeProduct = computed(() => slides.value[activeIndex.value] || null);

const selectSlide = (index: number) => {
  activeIndex.value = index;
};

const step = (direction: 1 | -1) => {
  if (!slides.value.length) {
    return;
  }
  activeIndex.value = (activeIndex.value + direction + slides.value.length) % slides.value.length;
};

onMounted(() => {
  if (slides.value.length <= 1) {
    return;
  }
  timer = setInterval(() => step(1), 5000);
});

onBeforeUnmount(() => {
  if (timer) {
    clearInterval(timer);
  }
});

watch(
  slides,
  (value) => {
    if (!value.length) {
      activeIndex.value = 0;
    } else if (activeIndex.value >= value.length) {
      activeIndex.value = 0;
    }
  },
  { immediate: true }
);
</script>

<template>
  <section v-if="activeProduct" class="space-y-4">
    <div class="overflow-hidden rounded-[2rem] bg-gradient-to-br from-ink via-slate-900 to-clay text-white shadow-soft">
      <div class="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
        <div class="flex flex-col justify-between p-7 sm:p-10">
          <div class="space-y-5">
            <div class="flex flex-wrap items-center gap-3">
              <span class="badge !bg-white !text-ink">Скидки дня</span>
              <span class="rounded-full border border-white/20 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-white/75">
                До -{{ activeProduct.discount_percent }}%
              </span>
            </div>

            <div class="space-y-3">
              <p class="text-sm uppercase tracking-[0.18em] text-white/65">
                {{ formatCategoryName(activeProduct.category.name) }}
              </p>
              <h1 class="max-w-2xl font-display text-3xl font-bold tracking-tight sm:text-5xl">
                {{ activeProduct.name }}
              </h1>
              <p class="max-w-xl text-sm leading-7 text-white/75 sm:text-base">
                Реальные предложения от продавцов маркетплейса. Сравнивайте цену, скидку и выбирайте подходящего продавца прямо внутри товара.
              </p>
            </div>

            <div class="flex flex-wrap items-end gap-4">
              <div>
                <p class="text-3xl font-extrabold sm:text-5xl">{{ formatMoney(activeProduct.price) }}</p>
                <p class="mt-1 text-base text-white/45 line-through">{{ formatMoney(activeProduct.old_price) }}</p>
              </div>
              <div class="rounded-2xl bg-white/10 px-4 py-3 text-sm text-white/75">
                <p>Продавец</p>
                <p class="mt-1 font-semibold text-white">{{ activeProduct.seller.shop_name }}</p>
              </div>
            </div>
          </div>

          <div class="mt-8 flex flex-wrap gap-3">
            <NuxtLink :to="`/products/${activeProduct.id}`" class="inline-flex items-center rounded-2xl bg-white px-5 py-3 text-sm font-semibold text-ink transition hover:bg-slate-100">
              Смотреть предложение
            </NuxtLink>
            <NuxtLink to="/#catalog" class="inline-flex items-center rounded-2xl border border-white/20 px-5 py-3 text-sm font-semibold text-white transition hover:bg-white/10">
              Перейти в каталог
            </NuxtLink>
          </div>
        </div>

        <div class="relative min-h-[280px] overflow-hidden lg:min-h-[420px]">
          <img :src="activeProduct.image_url" :alt="activeProduct.name" class="h-full w-full object-cover" />
          <div class="absolute inset-0 bg-gradient-to-t from-slate-950/45 via-transparent to-transparent" />

          <div class="absolute bottom-5 right-5 flex gap-2">
            <button
              type="button"
              class="flex h-11 w-11 items-center justify-center rounded-full border border-white/25 bg-white/10 text-lg text-white transition hover:bg-white/20"
              @click="step(-1)"
            >
              ‹
            </button>
            <button
              type="button"
              class="flex h-11 w-11 items-center justify-center rounded-full border border-white/25 bg-white/10 text-lg text-white transition hover:bg-white/20"
              @click="step(1)"
            >
              ›
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <button
        v-for="(slide, index) in slides"
        :key="slide.id"
        type="button"
        class="panel flex items-center gap-3 p-3 text-left transition hover:-translate-y-0.5"
        :class="index === activeIndex ? 'ring-2 ring-clay/40' : ''"
        @click="selectSlide(index)"
      >
        <img :src="slide.image_url" :alt="slide.name" class="h-20 w-20 rounded-2xl object-cover" />
        <div class="min-w-0">
          <p class="line-clamp-2 text-sm font-semibold text-ink">{{ slide.name }}</p>
          <p class="mt-2 text-sm font-bold text-clay">-{{ slide.discount_percent }}%</p>
          <p class="text-xs text-slate-500">{{ formatMoney(slide.price) }}</p>
        </div>
      </button>
    </div>
  </section>
</template>
