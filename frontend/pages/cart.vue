<script setup lang="ts">
import type { Order } from "~/types";
import { useApiError } from "~/composables/useApiError";
import { useApiClient } from "~/composables/useApiClient";
import { useFormatters } from "~/composables/useFormatters";
import { useAuthStore } from "~/stores/auth";
import { useCartStore } from "~/stores/cart";
import { useNotificationsStore } from "~/stores/notifications";

interface Branch {
  id: number;
  name: string;
  city: string;
  address: string;
  latitude: string;
  longitude: string;
  working_hours: string;
}

const auth = useAuthStore();
const cartStore = useCartStore();
const api = useApiClient();
const notifications = useNotificationsStore();
const { getErrorMessage } = useApiError();
const { formatMoney, formatPaymentMethod } = useFormatters();

const orderSuccess = ref<Order | null>(null);
const orderError = ref("");
const pageError = ref("");
const branches = ref<Branch[]>([]);

const ASTANA_CITY_NAMES = ["астана", "нур-султан"];

const checkoutForm = reactive({
  payment_method: "card_on_delivery" as "cash_on_delivery" | "card_on_delivery" | "card_online",
  delivery_method: "courier" as "courier" | "pickup",
  delivery_address: "",
  branch_id: null as number | null,
});

await auth.bootstrap();
if (auth.loggedIn) {
  try {
    await cartStore.fetchCart();
  } catch (error: any) {
    pageError.value = getErrorMessage(error, "Не удалось загрузить корзину.");
  }
}

// Загружаем филиалы
try {
  const res = await api.get<any>("/branches/");
  branches.value = Array.isArray(res) ? res : (res?.results ?? []);
} catch {}

const astanaBranches = computed(() =>
  branches.value.filter((branch) => ASTANA_CITY_NAMES.includes((branch.city || "").trim().toLowerCase()))
);

const selectedBranch = computed(() =>
  astanaBranches.value.find((b) => b.id === checkoutForm.branch_id) || null
);

const onSelectBranch = (branch: Branch) => {
  checkoutForm.branch_id = branch.id;
};

// Переключение способа доставки
watch(() => checkoutForm.delivery_method, (val) => {
  if (val === "courier") {
    checkoutForm.branch_id = null;
  } else {
    checkoutForm.delivery_address = "";
    if (checkoutForm.branch_id && !astanaBranches.value.some((branch) => branch.id === checkoutForm.branch_id)) {
      checkoutForm.branch_id = null;
    }
  }
});

const canCheckout = computed(() => {
  if (!cartStore.cart?.items?.length) return false;
  if (checkoutForm.delivery_method === "courier" && !checkoutForm.delivery_address.trim()) return false;
  if (checkoutForm.delivery_method === "pickup" && !checkoutForm.branch_id) return false;
  return true;
});

const checkout = async () => {
  if (!auth.loggedIn) return navigateTo("/login");
  orderError.value = "";
  try {
    orderSuccess.value = await api.post<Order>("/orders/create/", {
      payment_method: checkoutForm.payment_method,
      delivery_method: checkoutForm.delivery_method,
      delivery_address: checkoutForm.delivery_address,
      branch_id: checkoutForm.branch_id,
    });
    if (checkoutForm.payment_method === "card_online") {
      const response = await api.post<{ checkout_url: string }>(`/orders/${orderSuccess.value.id}/checkout/`);
      if (process.client) window.location.href = response.checkout_url;
      return;
    }
    await cartStore.fetchCart();
    notifications.success("Заказ успешно создан.");
  } catch (error: any) {
    orderError.value = getErrorMessage(error, "Не удалось создать заказ.");
  }
};

const updateItemQuantity = async (itemId: number, quantity: number) => {
  try { await cartStore.updateItem(itemId, quantity); } catch {}
};

const removeItem = async (itemId: number) => {
  try { await cartStore.removeItem(itemId); } catch {}
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
      <div v-if="pageError" class="panel border border-rose-200 p-5 text-sm text-rose-500">{{ pageError }}</div>

      <!-- Успешный заказ -->
      <div v-if="orderSuccess" class="panel border border-pine/20 p-6">
        <p class="text-sm font-semibold uppercase tracking-[0.16em] text-pine">Заказ создан</p>
        <h2 class="mt-3 font-display text-2xl font-bold text-ink">Заказ #{{ orderSuccess.id }} принят</h2>
        <p class="mt-2 text-sm text-slate-500">Итого: {{ formatMoney(orderSuccess.total_amount) }}</p>
        <p class="mt-1 text-sm text-slate-500">Оплата: {{ formatPaymentMethod(orderSuccess.payment_method) }}</p>
        <p v-if="(orderSuccess as any).delivery_method === 'pickup'" class="mt-1 text-sm text-slate-500">
          📍 Самовывоз: {{ (orderSuccess as any).branch?.address || 'филиал выбран' }}
        </p>
        <p v-else class="mt-1 text-sm text-slate-500">
          🚚 Доставка: {{ (orderSuccess as any).delivery_address }}
        </p>
        <NuxtLink to="/account/orders" class="btn-primary mt-5">Перейти к истории заказов</NuxtLink>
      </div>

      <div v-if="orderError" class="panel border border-rose-200 p-5 text-sm text-rose-500">{{ orderError }}</div>

      <div class="grid gap-6 lg:grid-cols-[1fr_360px]">
        <!-- Список товаров -->
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

        <!-- Форма оформления -->
        <aside class="space-y-4 h-fit">

          <!-- Способ доставки -->
          <div class="panel p-5 space-y-4">
            <p class="text-sm font-semibold uppercase tracking-[0.12em] text-slate-500">Доставка</p>
            <div class="grid grid-cols-2 gap-2">
              <button
                type="button"
                class="flex flex-col items-center gap-2 rounded-xl border-2 p-4 text-sm font-medium transition"
                :class="checkoutForm.delivery_method === 'courier'
                  ? 'border-clay bg-clay/5 text-clay'
                  : 'border-slate-100 text-slate-500 hover:border-slate-300'"
                @click="checkoutForm.delivery_method = 'courier'"
              >
                <span class="text-2xl">🚚</span>
                Курьером
              </button>
              <button
                type="button"
                class="flex flex-col items-center gap-2 rounded-xl border-2 p-4 text-sm font-medium transition"
                :class="checkoutForm.delivery_method === 'pickup'
                  ? 'border-clay bg-clay/5 text-clay'
                  : 'border-slate-100 text-slate-500 hover:border-slate-300'"
                @click="checkoutForm.delivery_method = 'pickup'"
              >
                <span class="text-2xl">🏪</span>
                Самовывоз
              </button>
            </div>

            <!-- Адрес курьера -->
            <div v-if="checkoutForm.delivery_method === 'courier'" class="space-y-2">
              <label class="block text-sm font-medium text-ink">Адрес доставки</label>
              <input
                v-model="checkoutForm.delivery_address"
                type="text"
                placeholder="Город, улица, дом, квартира"
                class="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-clay focus:ring-2 focus:ring-clay/20"
              />
            </div>

            <!-- Самовывоз: карта -->
            <div v-if="checkoutForm.delivery_method === 'pickup'" class="space-y-3">
              <!-- Выбранный филиал -->
              <div v-if="selectedBranch" class="rounded-xl bg-clay/5 border border-clay/20 p-3">
                <p class="text-sm font-semibold text-clay">✓ {{ selectedBranch.name }}</p>
                <p class="mt-1 text-xs text-slate-500">📍 {{ selectedBranch.address }}</p>
                <p class="text-xs text-slate-500">🕐 {{ selectedBranch.working_hours }}</p>
              </div>
              <p v-else-if="astanaBranches.length" class="text-xs text-slate-400">Выберите пункт выдачи на карте</p>
              <p v-else class="text-xs text-slate-400">Самовывоз доступен только в Астане.</p>

              <!-- Карта -->
              <ClientOnly v-if="astanaBranches.length">
                <BranchMap
                  :branches="astanaBranches"
                  :selected-branch-id="checkoutForm.branch_id"
                  @select="onSelectBranch"
                />
              </ClientOnly>

              <!-- Список филиалов -->
              <div v-if="astanaBranches.length" class="max-h-48 overflow-y-auto space-y-2">
                <button
                  v-for="branch in astanaBranches"
                  :key="branch.id"
                  type="button"
                  class="w-full rounded-xl border-2 p-3 text-left text-sm transition"
                  :class="checkoutForm.branch_id === branch.id
                    ? 'border-clay bg-clay/5'
                    : 'border-slate-100 hover:border-slate-300'"
                  @click="onSelectBranch(branch)"
                >
                  <p class="font-semibold text-ink">{{ branch.name }}</p>
                  <p class="mt-0.5 text-xs text-slate-500">{{ branch.address }} · {{ branch.working_hours }}</p>
                </button>
              </div>
            </div>
          </div>

          <!-- Способ оплаты -->
          <div class="panel p-5 space-y-3">
            <p class="text-sm font-semibold uppercase tracking-[0.12em] text-slate-500">Оплата</p>
            <label class="flex items-start gap-3 cursor-pointer">
              <input v-model="checkoutForm.payment_method" type="radio" class="mt-1" value="cash_on_delivery" />
              <span>
                <span class="block font-medium text-ink text-sm">Наличными при получении</span>
                <span class="block text-xs text-slate-500">Покупатель оплачивает заказ при вручении.</span>
              </span>
            </label>
            <label class="flex items-start gap-3 cursor-pointer">
              <input v-model="checkoutForm.payment_method" type="radio" class="mt-1" value="card_on_delivery" />
              <span>
                <span class="block font-medium text-ink text-sm">Картой при получении</span>
                <span class="block text-xs text-slate-500">Оплата через терминал курьера или в пункте выдачи.</span>
              </span>
            </label>
            <label class="flex items-start gap-3 cursor-pointer">
              <input v-model="checkoutForm.payment_method" type="radio" class="mt-1" value="card_online" />
              <span>
                <span class="block font-medium text-ink text-sm">Онлайн картой (Stripe)</span>
                <span class="block text-xs text-slate-500">После оформления вы перейдёте на защищённую страницу Stripe.</span>
              </span>
            </label>
          </div>

          <!-- Итог и кнопка -->
          <div class="panel p-5 space-y-4">
            <div class="space-y-2 text-sm text-slate-500">
              <div class="flex justify-between">
                <span>Товаров</span>
                <span>{{ cartStore.cart?.total_items || 0 }}</span>
              </div>
              <div class="flex justify-between text-lg font-bold text-ink">
                <span>Итого</span>
                <span>{{ formatMoney(cartStore.totalAmount) }}</span>
              </div>
            </div>
            <button
              class="btn-primary w-full disabled:opacity-40 disabled:cursor-not-allowed"
              type="button"
              :disabled="!canCheckout"
              @click="checkout"
            >
              Оформить заказ
            </button>
            <p v-if="checkoutForm.delivery_method === 'courier' && !checkoutForm.delivery_address.trim()" class="text-xs text-center text-slate-400">
              Укажите адрес доставки
            </p>
            <p v-if="checkoutForm.delivery_method === 'pickup' && !checkoutForm.branch_id" class="text-xs text-center text-slate-400">
              Выберите пункт выдачи на карте
            </p>
          </div>
        </aside>
      </div>
    </template>
  </div>
</template>
