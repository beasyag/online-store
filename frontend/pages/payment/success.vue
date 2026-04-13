<script setup lang="ts">
import type { Order } from "~/types";
import { useApiClient } from "~/composables/useApiClient";
import { useApiError } from "~/composables/useApiError";
import { useFormatters } from "~/composables/useFormatters";
import { useAuthStore } from "~/stores/auth";
import { useNotificationsStore } from "~/stores/notifications";

const route = useRoute();
const auth = useAuthStore();
const api = useApiClient();
const notifications = useNotificationsStore();
const { getErrorMessage } = useApiError();
const { formatMoney, formatPaymentMethod } = useFormatters();

const order = ref<Order | null>(null);
const errorMessage = ref("");
const sessionId = computed(() => String(route.query.session_id || ""));

await auth.bootstrap();

if (!auth.loggedIn) {
  await navigateTo("/login");
}

if (sessionId.value) {
  try {
    order.value = await api.post<Order>("/orders/checkout/confirm/", { session_id: sessionId.value });
    notifications.success("Оплата подтверждена.");
  } catch (error: any) {
    errorMessage.value = getErrorMessage(error, "Не удалось подтвердить оплату.");
  }
} else {
  errorMessage.value = "Отсутствует идентификатор платёжной сессии.";
}
</script>

<template>
  <div class="shell max-w-3xl">
    <div v-if="order" class="panel border border-pine/20 p-8">
      <span class="badge !bg-pine/10 !text-pine">Оплата успешна</span>
      <h1 class="section-title mt-4">Заказ #{{ order.id }} оплачен</h1>
      <p class="mt-3 text-sm text-slate-500">Сумма: {{ formatMoney(order.total_amount) }}</p>
      <p class="mt-1 text-sm text-slate-500">Способ оплаты: {{ formatPaymentMethod(order.payment_method) }}</p>
      <div class="mt-6 flex flex-wrap gap-3">
        <NuxtLink to="/account/orders" class="btn-primary">История заказов</NuxtLink>
        <NuxtLink to="/" class="btn-secondary">На главную</NuxtLink>
      </div>
    </div>

    <div v-else class="panel border border-rose-200 p-8">
      <span class="badge !bg-rose-100 !text-rose-600">Ошибка оплаты</span>
      <h1 class="section-title mt-4">Подтверждение не прошло</h1>
      <p class="mt-3 text-sm text-rose-500">{{ errorMessage }}</p>
      <div class="mt-6 flex flex-wrap gap-3">
        <NuxtLink to="/account/orders" class="btn-primary">К заказам</NuxtLink>
        <NuxtLink to="/cart" class="btn-secondary">В корзину</NuxtLink>
      </div>
    </div>
  </div>
</template>
