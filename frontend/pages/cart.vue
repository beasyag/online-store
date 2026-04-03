<script setup lang="ts">
import type { Order } from "~/types";
import { useApiError } from "~/composables/useApiError";
import { useApiClient } from "~/composables/useApiClient";
import { useFormatters } from "~/composables/useFormatters";
import { useAuthStore } from "~/stores/auth";
import { useCartStore } from "~/stores/cart";
import { useNotificationsStore } from "~/stores/notifications";

const auth = useAuthStore();
const cartStore = useCartStore();
const api = useApiClient();
const notifications = useNotificationsStore();
const { getErrorMessage } = useApiError();
const { formatMoney } = useFormatters();

const orderSuccess = ref<Order | null>(null);
const orderError = ref("");
const pageError = ref("");

await auth.bootstrap();
if (auth.loggedIn) {
  try {
    await cartStore.fetchCart();
  } catch (error: any) {
    pageError.value = getErrorMessage(error, "Не удалось загрузить корзину.");
  }
}

const checkout = async () => {
  if (!auth.loggedIn) {
    return navigateTo("/login");
  }
  orderError.value = "";
  try {
    orderSuccess.value = await api.post<Order>("/orders/create/");
    await cartStore.fetchCart();
    notifications.success("Заказ успешно создан.");
  } catch (error: any) {
    orderError.value = getErrorMessage(error, "Не удалось создать заказ.");
  }
};

const updateItemQuantity = async (itemId: number, quantity: number) => {
  try {
    await cartStore.updateItem(itemId, quantity);
  } catch {}
};

const removeItem = async (itemId: number) => {
  try {
    await cartStore.removeItem(itemId);
  } catch {}
};
</script>

<template>
  <div class="shell space-y-8">
    <section class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <span class="badge !bg-clay">Корзина</span>
        <h1 class="section-title mt-3">Выбранные товары</h1>
      </div>
      <p class="text-sm text-slate-500">Проверьте количество товаров перед оформлением multi-vendor заказа.</p>
    </section>

    <div v-if="!auth.loggedIn" class="panel p-8 text-center">
      <p class="text-sm text-slate-500">Войдите, чтобы управлять корзиной и оформлять заказы.</p>
      <NuxtLink to="/login" class="btn-primary mt-4">Войти</NuxtLink>
    </div>

    <template v-else>
      <div v-if="pageError" class="panel border border-rose-200 p-5 text-sm text-rose-500">
        {{ pageError }}
      </div>

      <div v-if="orderSuccess" class="panel border border-pine/20 p-6">
        <p class="text-sm font-semibold uppercase tracking-[0.16em] text-pine">Заказ создан</p>
        <h2 class="mt-3 font-display text-2xl font-bold text-ink">Заказ #{{ orderSuccess.id }} принят в обработку</h2>
        <p class="mt-2 text-sm text-slate-500">Итого: {{ formatMoney(orderSuccess.total_amount) }}</p>
        <NuxtLink to="/account/orders" class="btn-primary mt-5">Перейти к истории заказов</NuxtLink>
      </div>

      <div v-if="orderError" class="panel border border-rose-200 p-5 text-sm text-rose-500">
        {{ orderError }}
      </div>

      <div class="grid gap-6 lg:grid-cols-[1fr_340px]">
        <div class="space-y-4">
          <CartItemCard
            v-for="item in cartStore.cart?.items || []"
            :key="item.id"
            :item="item"
            @remove="removeItem(item.id)"
            @update-quantity="updateItemQuantity(item.id, $event)"
          />
          <div v-if="!(cartStore.cart?.items?.length)" class="panel p-8 text-center text-sm text-slate-500">
            Корзина пуста. Вернитесь в каталог и добавьте несколько товаров.
          </div>
        </div>

        <aside class="panel h-fit space-y-5 p-6">
          <div>
            <p class="text-sm font-semibold uppercase tracking-[0.16em] text-slate-500">Итог</p>
            <h2 class="mt-2 font-display text-2xl font-bold text-ink">Оформление</h2>
          </div>
          <div class="space-y-3 text-sm text-slate-500">
            <div class="flex items-center justify-between">
              <span>Товаров</span>
              <span>{{ cartStore.cart?.total_items || 0 }}</span>
            </div>
            <div class="flex items-center justify-between text-lg font-bold text-ink">
              <span>Итого</span>
              <span>{{ formatMoney(cartStore.totalAmount) }}</span>
            </div>
          </div>
          <button class="btn-primary w-full" type="button" :disabled="!(cartStore.cart?.items?.length)" @click="checkout">
            Оформить заказ
          </button>
        </aside>
      </div>
    </template>
  </div>
</template>
