<script setup lang="ts">
import { useApiError } from "~/composables/useApiError";
import { useAuthStore } from "~/stores/auth";

const auth = useAuthStore();
const { getErrorMessage } = useApiError();
const config = useRuntimeConfig();

const form = reactive({
  username: "",
  password: ""
});
const errorMessage = ref("");
const googleButtonRef = ref<HTMLElement | null>(null);
const googleReady = ref(false);
const googleClientId = config.public.googleClientId;

declare global {
  interface Window {
    google?: any;
  }
}

const handleGoogleCredential = async (response: { credential?: string }) => {
  if (!response?.credential) {
    errorMessage.value = "Google не вернул токен авторизации.";
    return;
  }

  errorMessage.value = "";
  try {
    await auth.googleLogin(response.credential);
    navigateTo("/");
  } catch (error: any) {
    errorMessage.value = getErrorMessage(error, "Не удалось выполнить вход через Google.");
  }
};

const renderGoogleButton = () => {
  if (!process.client || !googleClientId || !googleButtonRef.value || !window.google?.accounts?.id) {
    return;
  }

  const buttonWidth = Math.min(320, Math.max(220, googleButtonRef.value.clientWidth || 320));

  googleButtonRef.value.innerHTML = "";
  window.google.accounts.id.initialize({
    client_id: googleClientId,
    callback: handleGoogleCredential
  });
  window.google.accounts.id.renderButton(googleButtonRef.value, {
    theme: "outline",
    size: "large",
    shape: "pill",
    text: "signin_with",
    width: buttonWidth
  });
  googleReady.value = true;
};

onMounted(() => {
  if (!googleClientId) {
    return;
  }

  if (window.google?.accounts?.id) {
    renderGoogleButton();
    return;
  }

  const existingScript = document.querySelector<HTMLScriptElement>('script[data-google-identity="true"]');
  if (existingScript) {
    existingScript.addEventListener("load", renderGoogleButton, { once: true });
    return;
  }

  const script = document.createElement("script");
  script.src = "https://accounts.google.com/gsi/client";
  script.async = true;
  script.defer = true;
  script.dataset.googleIdentity = "true";
  script.addEventListener("load", renderGoogleButton, { once: true });
  document.head.appendChild(script);
});

const submit = async () => {
  errorMessage.value = "";
  try {
    await auth.login(form);
    navigateTo("/");
  } catch (error: any) {
    errorMessage.value = getErrorMessage(error, "Не удалось выполнить вход. Проверьте логин и пароль.");
  }
};
</script>

<template>
  <div class="shell max-w-2xl">
    <div class="panel p-8 sm:p-10">
      <span class="badge">Вход</span>
      <h1 class="section-title mt-4">Войти в аккаунт</h1>
      <p class="mt-2 text-sm text-slate-500">Используйте тестовый аккаунт покупателя, продавца или администратора.</p>

      <div v-if="googleClientId" class="mt-8 flex flex-col items-center gap-3">
        <div ref="googleButtonRef" class="min-h-[44px] w-full max-w-[320px]" />
        <p v-if="!googleReady" class="text-xs text-slate-500">Загружаем Google Sign-In...</p>
      </div>

      <div v-if="googleClientId" class="mt-6 flex items-center gap-4 text-xs uppercase tracking-[0.28em] text-slate-400">
        <div class="h-px flex-1 bg-slate-200" />
        <span>или</span>
        <div class="h-px flex-1 bg-slate-200" />
      </div>

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
