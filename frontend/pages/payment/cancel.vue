<script setup lang="ts">
import type { Order, StripeCheckoutResponse } from "~/types";
import { useApiClient } from "~/composables/useApiClient";
import { useApiError } from "~/composables/useApiError";
import { useFormatters } from "~/composables/useFormatters";
import { useAuthStore } from "~/stores/auth";

const route = useRoute();
const auth = useAuthStore();
const api = useApiClient();
const { getErrorMessage } = useApiError();
const { formatMoney, formatPaymentMethod } = useFormatters();

const order = ref<Order | null>(null);
const errorMessage = ref("");
const retryPending = ref(false);
const orderId = computed(() => Number(route.query.order_id || 0));

await auth.bootstrap();

if (!auth.loggedIn) {
  await navigateTo("/login");
}

if (orderId.value) {
  try {
    order.value = await api.get<Order>(`/orders/${orderId.value}/`);
  } catch (error: any) {
    errorMessage.value = getErrorMessage(error, "Не удалось загрузить заказ.");
  }
} else {
  errorMessage.value = "Не передан идентификатор заказа.";
}

const retryPayment = async () => {
  if (!order.value) {
    return;
  }
  retryPending.value = true;
  errorMessage.value = "";
  try {
    const response = await api.post<StripeCheckoutResponse>(`/orders/${order.value.id}/checkout/`);
    if (process.client) {
      window.location.href = response.checkout_url;
    }
  } catch (error: any) {
    errorMessage.value = getErrorMessage(error, "Не удалось повторно открыть Stripe Checkout.");
  } finally {
    retryPending.value = false;
  }
};
</script>

<template>
  <div class="shell max-w-3xl">
    <div class="panel p-8">
      <span class="badge !bg-clay">Оплата прервана</span>
      <h1 class="section-title mt-4">Платёж не завершён</h1>

      <template v-if="order">
        <p class="mt-3 text-sm text-slate-500">Заказ #{{ order.id }} сохранён со статусом ожидания оплаты.</p>
        <p class="mt-1 text-sm text-slate-500">Сумма: {{ formatMoney(order.total_amount) }}</p>
        <p class="mt-1 text-sm text-slate-500">Способ оплаты: {{ formatPaymentMethod(order.payment_method) }}</p>
        <div class="mt-6 flex flex-wrap gap-3">
          <button class="btn-primary" type="button" :disabled="retryPending" @click="retryPayment">
            {{ retryPending ? "Переходим..." : "Повторить оплату" }}
          </button>
          <NuxtLink to="/account/orders" class="btn-secondary">К заказам</NuxtLink>
        </div>
      </template>

      <p v-if="errorMessage" class="mt-4 text-sm text-rose-500">{{ errorMessage }}</p>
    </div>
  </div>
</template>
