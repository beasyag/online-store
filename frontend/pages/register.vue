<script setup lang="ts">
import { useApiError } from "~/composables/useApiError";
import { useAuthStore } from "~/stores/auth";

const auth = useAuthStore();
const { getErrorMessage } = useApiError();

const form = reactive({
  username: "",
  email: "",
  password: "",
  first_name: "",
  last_name: "",
  role: "buyer" as "buyer" | "seller",
  shop_name: "",
  shop_description: "",
  shop_avatar: ""
});
const errorMessage = ref("");

const submit = async () => {
  errorMessage.value = "";
  try {
    await auth.register(form);
    navigateTo("/");
  } catch (error: any) {
    errorMessage.value = getErrorMessage(error, "Не удалось зарегистрироваться. Проверьте заполнение формы.");
  }
};
</script>

<template>
  <div class="shell max-w-3xl">
    <div class="panel p-8 sm:p-10">
      <span class="badge !bg-clay">Регистрация</span>
      <h1 class="section-title mt-4">Создать аккаунт</h1>
      <p class="mt-2 text-sm text-slate-500">Зарегистрируйтесь как покупатель или сразу откройте магазин продавца.</p>

      <form class="mt-8 grid gap-5 md:grid-cols-2" @submit.prevent="submit">
        <div class="space-y-2">
          <label class="text-sm font-semibold text-ink">Логин</label>
          <input v-model="form.username" class="field" required />
        </div>
        <div class="space-y-2">
          <label class="text-sm font-semibold text-ink">Email</label>
          <input v-model="form.email" class="field" required type="email" />
        </div>
        <div class="space-y-2">
          <label class="text-sm font-semibold text-ink">Имя</label>
          <input v-model="form.first_name" class="field" />
        </div>
        <div class="space-y-2">
          <label class="text-sm font-semibold text-ink">Фамилия</label>
          <input v-model="form.last_name" class="field" />
        </div>
        <div class="space-y-2">
          <label class="text-sm font-semibold text-ink">Пароль</label>
          <input v-model="form.password" class="field" required type="password" />
        </div>
        <div class="space-y-2">
          <label class="text-sm font-semibold text-ink">Роль</label>
          <select v-model="form.role" class="field">
            <option value="buyer">Покупатель</option>
            <option value="seller">Продавец</option>
          </select>
        </div>

        <template v-if="form.role === 'seller'">
          <div class="space-y-2 md:col-span-2">
            <label class="text-sm font-semibold text-ink">Название магазина</label>
            <input v-model="form.shop_name" class="field" required />
          </div>
          <div class="space-y-2 md:col-span-2">
            <label class="text-sm font-semibold text-ink">Описание магазина</label>
            <textarea v-model="form.shop_description" rows="4" class="field" />
          </div>
          <div class="space-y-2 md:col-span-2">
            <label class="text-sm font-semibold text-ink">Ссылка на логотип</label>
            <input v-model="form.shop_avatar" class="field" type="url" />
          </div>
        </template>

        <p v-if="errorMessage" class="text-sm text-rose-500 md:col-span-2">{{ errorMessage }}</p>
        <button class="btn-primary md:col-span-2" type="submit">Создать аккаунт</button>
      </form>
    </div>
  </div>
</template>
