<script setup lang="ts">
import { useAuthStore } from "~/stores/auth";

const auth = useAuthStore();

const form = reactive({
  username: "",
  password: ""
});
const errorMessage = ref("");

const submit = async () => {
  errorMessage.value = "";
  try {
    await auth.login(form);
    navigateTo("/");
  } catch (error: any) {
    errorMessage.value = error?.data?.detail || "Не удалось выполнить вход.";
  }
};
</script>

<template>
  <div class="shell max-w-2xl">
    <div class="panel p-8 sm:p-10">
      <span class="badge">Вход</span>
      <h1 class="section-title mt-4">Войти в аккаунт</h1>
      <p class="mt-2 text-sm text-slate-500">Используйте тестовый аккаунт покупателя, продавца или администратора.</p>

      <form class="mt-8 space-y-5" @submit.prevent="submit">
        <div class="space-y-2">
          <label class="text-sm font-semibold text-ink">Логин</label>
          <input v-model="form.username" class="field" required />
        </div>
        <div class="space-y-2">
          <label class="text-sm font-semibold text-ink">Пароль</label>
          <input v-model="form.password" class="field" required type="password" />
        </div>
        <p v-if="errorMessage" class="text-sm text-rose-500">{{ errorMessage }}</p>
        <button class="btn-primary w-full" type="submit">Войти</button>
      </form>
    </div>
  </div>
</template>
