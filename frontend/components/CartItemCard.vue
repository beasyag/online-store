<script setup lang="ts">
import type { CartItem } from "~/types";
import { useFormatters } from "~/composables/useFormatters";

const props = defineProps<{
  item: CartItem;
}>();

const emit = defineEmits<{
  updateQuantity: [quantity: number];
  remove: [];
}>();

const quantity = ref(props.item.quantity);
const { formatMoney } = useFormatters();

watch(
  () => props.item.quantity,
  (value) => {
    quantity.value = value;
  }
);
</script>

<template>
  <article class="panel flex flex-col gap-4 p-5 sm:flex-row sm:items-center">
    <img :src="item.product.image_url" :alt="item.product.name" class="h-28 w-full rounded-2xl object-cover sm:w-32" />
    <div class="min-w-0 flex-1">
      <NuxtLink :to="`/products/${item.product.id}`" class="text-lg font-bold text-ink">
        {{ item.product.name }}
      </NuxtLink>
      <p class="mt-1 text-sm text-slate-500">{{ item.product.seller.shop_name }}</p>
      <p class="mt-3 text-sm font-semibold text-ink">{{ formatMoney(item.product.price) }}</p>
    </div>
    <div class="flex items-center gap-3">
      <input v-model.number="quantity" min="1" type="number" class="field w-24" />
      <button class="btn-secondary !px-4 !py-3" type="button" @click="emit('updateQuantity', quantity)">
        Обновить
      </button>
      <button class="text-sm font-semibold text-rose-500" type="button" @click="emit('remove')">
        Удалить
      </button>
    </div>
    <div class="text-right">
      <p class="text-sm text-slate-500">Сумма</p>
      <p class="text-lg font-bold text-ink">{{ formatMoney(item.subtotal) }}</p>
    </div>
  </article>
</template>
