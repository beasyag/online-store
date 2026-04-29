<script setup lang="ts">
import type { Product } from "~/types";
import { useFormatters } from "~/composables/useFormatters";

const props = defineProps<{
  products: Product[];
}>();

const { formatMoney, formatCategoryName } = useFormatters();
const activeIndex = ref(0);
const isMobileSlider = ref(false);
let timer: ReturnType<typeof setInterval> | null = null;
const touchStartX = ref<number | null>(null);
const touchDeltaX = ref(0);

const slides = computed(() =>
  props.products.filter((product) => product.old_price && (product.discount_percent || 0) > 0).slice(0, 6)
);
const activeProduct = computed(() => slides.value[activeIndex.value] || null);
const totalSlides = computed(() => slides.value.length);

const updateSliderMode = () => {
  if (!process.client) {
    return;
  }
  isMobileSlider.value = window.innerWidth < 1024;
};

const selectSlide = (index: number) => {
  activeIndex.value = index;
};

const step = (direction: 1 | -1) => {
  if (!totalSlides.value) {
    return;
  }
  activeIndex.value = (activeIndex.value + direction + totalSlides.value) % totalSlides.value;
};

const onTouchStart = (event: TouchEvent) => {
  touchStartX.value = event.touches[0]?.clientX ?? null;
  touchDeltaX.value = 0;
};

const onTouchMove = (event: TouchEvent) => {
  if (touchStartX.value === null) {
    return;
  }
  touchDeltaX.value = (event.touches[0]?.clientX ?? touchStartX.value) - touchStartX.value;
};

const onTouchEnd = () => {
  if (touchStartX.value === null) {
    return;
  }

  if (Math.abs(touchDeltaX.value) > 48) {
    step(touchDeltaX.value < 0 ? 1 : -1);
  }

  touchStartX.value = null;
  touchDeltaX.value = 0;
};

onMounted(() => {
  updateSliderMode();
  window.addEventListener("resize", updateSliderMode);

  if (totalSlides.value <= 1) {
    return;
  }
  timer = setInterval(() => step(1), 5000);
});

onBeforeUnmount(() => {
  if (process.client) {
    window.removeEventListener("resize", updateSliderMode);
  }
  if (timer) {
    clearInterval(timer);
  }
});

watch(
  slides,
  (value) => {
    const maxIndex = Math.max(totalSlides.value - 1, 0);
    if (!value.length) {
      activeIndex.value = 0;
    } else if (activeIndex.value > maxIndex) {
      activeIndex.value = maxIndex;
    }
  },
  { immediate: true }
);
</script>

<template>
  <section v-if="slides.length && activeProduct" class="space-y-4">
    <div
      v-if="isMobileSlider"
      class="overflow-hidden rounded-[1.6rem] border border-white/80 bg-white/95 shadow-soft"
      @touchstart.passive="onTouchStart"
      @touchmove.passive="onTouchMove"
      @touchend="onTouchEnd"
      @touchcancel="onTouchEnd"
    >
      <div class="space-y-4 p-4">
        <div class="space-y-2">
          <div class="flex flex-wrap gap-2">
            <span class="badge !bg-clay">Скидки дня</span>
            <span v-if="activeProduct.discount_percent" class="badge !bg-white !text-ink">-{{ activeProduct.discount_percent }}%</span>
          </div>
          <p class="text-[11px] uppercase tracking-[0.18em] text-slate-500">{{ formatCategoryName(activeProduct.category.name) }}</p>
          <h2 class="line-clamp-2 font-display text-xl font-bold leading-tight text-ink">{{ activeProduct.name }}</h2>
        </div>

        <NuxtLink :to="`/products/${activeProduct.id}`" class="block overflow-hidden rounded-[1.2rem]">
          <div class="relative aspect-[16/10] overflow-hidden bg-white">
            <img :src="activeProduct.image_url" :alt="activeProduct.name" class="h-full w-full object-cover transition duration-300 hover:scale-[1.02]" />
            <div class="absolute inset-0 bg-gradient-to-t from-slate-950/35 via-transparent to-transparent" />
          </div>
        </NuxtLink>

        <div>
          <p class="text-2xl font-extrabold text-ink">{{ formatMoney(activeProduct.price) }}</p>
          <p class="mt-1 text-sm text-slate-400 line-through">{{ formatMoney(activeProduct.old_price) }}</p>
        </div>

        <NuxtLink
          :to="`/products/${activeProduct.id}`"
          class="inline-flex w-full items-center justify-center rounded-2xl bg-ink px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
        >
          Смотреть
        </NuxtLink>
      </div>

      <div v-if="slides.length > 1" class="flex items-center justify-center gap-2 border-t border-slate-100 px-4 py-4">
        <button
          v-for="(slide, index) in slides"
          :key="slide.id"
          type="button"
          class="h-2.5 rounded-full transition-all"
          :class="index === activeIndex ? 'w-7 bg-ink' : 'w-2.5 bg-slate-300'"
          :aria-label="`Переключить на мобильный слайд ${index + 1}`"
          @click="selectSlide(index)"
        />
      </div>
    </div>

    <div
      v-else
      class="overflow-hidden rounded-[1.6rem] bg-gradient-to-br from-ink via-slate-900 to-clay text-white shadow-soft sm:rounded-[2rem]"
      @touchstart.passive="onTouchStart"
      @touchmove.passive="onTouchMove"
      @touchend="onTouchEnd"
      @touchcancel="onTouchEnd"
    >
      <div class="grid gap-0 lg:grid-cols-[1.15fr_0.85fr] lg:gap-6">
        <div class="order-2 flex flex-col justify-between p-5 sm:p-10 lg:order-1">
          <div class="space-y-4 sm:space-y-5">
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
              <h1 class="max-w-2xl font-display text-[1.7rem] font-bold leading-tight tracking-tight sm:text-5xl">
                {{ activeProduct.name }}
              </h1>
              <p class="max-w-xl text-sm leading-6 text-white/75 sm:text-base sm:leading-7">
                Реальные предложения от продавцов маркетплейса. Сравнивайте цену, скидку и выбирайте подходящего продавца прямо внутри товара.
              </p>
            </div>

            <div class="flex flex-wrap items-end gap-3 sm:gap-4">
              <div>
                <p class="text-2xl font-extrabold sm:text-5xl">{{ formatMoney(activeProduct.price) }}</p>
                <p class="mt-1 text-sm text-white/45 line-through sm:text-base">{{ formatMoney(activeProduct.old_price) }}</p>
              </div>
              <div class="rounded-2xl bg-white/10 px-3 py-2 text-xs text-white/75 sm:px-4 sm:py-3 sm:text-sm">
                <p>Продавец</p>
                <p class="mt-1 font-semibold text-white">{{ activeProduct.seller.shop_name }}</p>
              </div>
            </div>
          </div>

          <div class="mt-6 flex flex-col gap-3 sm:mt-8 sm:flex-row sm:flex-wrap">
            <NuxtLink :to="`/products/${activeProduct.id}`" class="inline-flex items-center justify-center rounded-2xl bg-white px-5 py-3 text-sm font-semibold text-ink transition hover:bg-slate-100">
              Смотреть предложение
            </NuxtLink>
            <NuxtLink to="/catalog" class="inline-flex items-center justify-center rounded-2xl border border-white/20 px-5 py-3 text-sm font-semibold text-white transition hover:bg-white/10">
              Перейти в каталог
            </NuxtLink>
          </div>
        </div>

        <div class="relative order-1 min-h-[220px] overflow-hidden lg:order-2 lg:min-h-[420px]">
          <img :src="activeProduct.image_url" :alt="activeProduct.name" class="h-full w-full object-cover" />
          <div class="absolute inset-0 bg-gradient-to-t from-slate-950/45 via-slate-950/5 to-transparent lg:bg-gradient-to-t" />

          <div class="absolute bottom-4 right-4 hidden gap-2 sm:bottom-5 sm:right-5 lg:flex">
            <button
              type="button"
              class="flex h-10 w-10 items-center justify-center rounded-full border border-white/25 bg-white/10 text-lg text-white transition hover:bg-white/20 sm:h-11 sm:w-11"
              @click="step(-1)"
            >
              ‹
            </button>
            <button
              type="button"
              class="flex h-10 w-10 items-center justify-center rounded-full border border-white/25 bg-white/10 text-lg text-white transition hover:bg-white/20 sm:h-11 sm:w-11"
              @click="step(1)"
            >
              ›
            </button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
