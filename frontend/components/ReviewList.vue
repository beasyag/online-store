<script setup lang="ts">
import type { Review } from "~/types";
import { useFormatters } from "~/composables/useFormatters";

defineProps<{
  reviews: Review[];
}>();

const { formatDate } = useFormatters();
</script>

<template>
  <div class="space-y-4">
    <article v-for="review in reviews" :key="review.id" class="panel p-5">
      <div class="flex items-center justify-between gap-3">
        <div>
          <p class="font-semibold text-ink">{{ review.user.username }}</p>
          <p class="text-sm text-slate-500">{{ formatDate(review.created_at) }}</p>
        </div>
        <p class="font-semibold text-clay">Оценка {{ review.rating }}/5</p>
      </div>
      <p class="mt-3 text-sm leading-6 text-slate-600">{{ review.text }}</p>
    </article>

    <div v-if="!reviews.length" class="panel p-6 text-center text-sm text-slate-500">
      Здесь появятся отзывы после первых оценок покупателей.
    </div>
  </div>
</template>
