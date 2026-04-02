<script setup lang="ts">
import type { Product, Seller } from "~/types";
import { useApiClient } from "~/composables/useApiClient";
import { useFormatters } from "~/composables/useFormatters";
import { useAuthStore } from "~/stores/auth";

interface SellerDashboardResponse {
  product_count: number;
  orders_count: number;
  sales_count: number;
  total_sales: string;
  top_products: Product[];
  recent_orders: Array<{
    order_id: number;
    created_at: string;
    status: string;
    quantity: number;
    price_at_purchase: string;
    product: {
      id: number;
      name: string;
    };
  }>;
}

const auth = useAuthStore();
const api = useApiClient();
const { formatDate, formatMoney, formatOrderStatus } = useFormatters();

await auth.bootstrap();

const sellerProfile = ref<Seller | null>(null);
const dashboard = ref<SellerDashboardResponse | null>(null);
const loading = ref(false);
const errorMessage = ref("");

const form = reactive({
  shop_name: "",
  description: "",
  avatar: "https://picsum.photos/seed/new-seller/240/240"
});

const loadSellerData = async () => {
  if (!auth.loggedIn) {
    return;
  }
  loading.value = true;
  try {
    sellerProfile.value = await api.get<Seller>("/seller/profile/");
    dashboard.value = await api.get<SellerDashboardResponse>("/seller/dashboard/");
  } catch {
    sellerProfile.value = null;
    dashboard.value = null;
  } finally {
    loading.value = false;
  }
};

await loadSellerData();

const createProfile = async () => {
  errorMessage.value = "";
  try {
    await api.post("/seller/profile/", form);
    await auth.fetchProfile();
    await loadSellerData();
  } catch (error: any) {
    errorMessage.value = error?.data?.detail || "Не удалось создать профиль продавца.";
  }
};
</script>

<template>
  <div class="shell space-y-8">
    <section class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <span class="badge !bg-pine">Продавец</span>
        <h1 class="section-title mt-3">Кабинет продавца</h1>
      </div>
      <div class="flex flex-wrap gap-3">
        <NuxtLink to="/seller/products" class="btn-secondary">Мои товары</NuxtLink>
        <NuxtLink to="/seller/orders" class="btn-primary">Заказы продавца</NuxtLink>
      </div>
    </section>

    <div v-if="!auth.loggedIn" class="panel p-8 text-center text-sm text-slate-500">
      Войдите, чтобы открыть инструменты продавца.
    </div>

    <div v-else-if="loading" class="panel p-8 text-center text-sm text-slate-500">
      Загружаем кабинет продавца...
    </div>

    <template v-else-if="sellerProfile && dashboard">
      <section class="panel p-8">
        <div class="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
          <div class="flex items-center gap-4">
            <img :src="sellerProfile.avatar" :alt="sellerProfile.shop_name" class="h-20 w-20 rounded-3xl object-cover" />
            <div>
              <p class="text-sm uppercase tracking-[0.16em] text-slate-500">Магазин</p>
              <h2 class="font-display text-3xl font-bold text-ink">{{ sellerProfile.shop_name }}</h2>
              <p class="mt-2 max-w-2xl text-sm text-slate-500">{{ sellerProfile.description }}</p>
            </div>
          </div>
          <NuxtLink to="/seller/products/new" class="btn-primary">Добавить товар</NuxtLink>
        </div>
      </section>

      <DashboardWidgets :metrics="dashboard" />

      <section class="space-y-5">
        <div>
          <h2 class="section-title">Лучшие товары</h2>
          <p class="mt-2 text-sm text-slate-500">Лидеры по продажам и интересу покупателей.</p>
        </div>
        <ProductGrid :products="dashboard.top_products" empty-title="Лучшие товары появятся здесь" />
      </section>

      <section class="space-y-4">
        <div>
          <h2 class="section-title">Последние события по заказам</h2>
          <p class="mt-2 text-sm text-slate-500">Последние позиции заказов, в которых есть ваши товары.</p>
        </div>
        <div
          v-for="item in dashboard.recent_orders"
          :key="`${item.order_id}-${item.product.id}`"
          class="panel flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between"
        >
          <div>
            <p class="font-semibold text-ink">Заказ #{{ item.order_id }} • {{ item.product.name }}</p>
            <p class="text-sm text-slate-500">{{ formatOrderStatus(item.status) }}</p>
          </div>
          <div class="text-sm text-slate-500">
            <p>{{ item.quantity }} x {{ formatMoney(item.price_at_purchase) }}</p>
            <p>{{ formatDate(item.created_at) }}</p>
          </div>
        </div>
      </section>
    </template>

    <section v-else class="panel max-w-3xl p-8">
      <span class="badge !bg-clay">Стать продавцом</span>
      <h2 class="section-title mt-4">Создать профиль продавца</h2>
      <p class="mt-2 text-sm text-slate-500">
        Превратите аккаунт покупателя в магазин и начните управлять своими товарами.
      </p>

      <form class="mt-6 space-y-5" @submit.prevent="createProfile">
        <div class="space-y-2">
          <label class="text-sm font-semibold text-ink">Название магазина</label>
          <input v-model="form.shop_name" class="field" required />
        </div>
        <div class="space-y-2">
          <label class="text-sm font-semibold text-ink">Описание</label>
          <textarea v-model="form.description" rows="5" class="field" />
        </div>
        <div class="space-y-2">
          <label class="text-sm font-semibold text-ink">Ссылка на аватар</label>
          <input v-model="form.avatar" class="field" type="url" />
        </div>
        <p v-if="errorMessage" class="text-sm text-rose-500">{{ errorMessage }}</p>
        <button class="btn-primary" type="submit">Создать профиль продавца</button>
      </form>
    </section>
  </div>
</template>
