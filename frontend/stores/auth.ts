import type { User } from "~/types";
import { useApiClient } from "~/composables/useApiClient";
import { useCartStore } from "~/stores/cart";
import { useFavoritesStore } from "~/stores/favorites";

interface LoginPayload {
  username: string;
  password: string;
}

interface RegisterPayload {
  username: string;
  email: string;
  password: string;
  role: "buyer" | "seller";
  first_name?: string;
  last_name?: string;
  shop_name?: string;
  shop_description?: string;
  shop_avatar?: string;
}

interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

export const useAuthStore = defineStore("auth", () => {
  const accessTokenCookie = useCookie<string | null>("market_access_token", { sameSite: "lax" });
  const refreshTokenCookie = useCookie<string | null>("market_refresh_token", { sameSite: "lax" });
  const user = ref<User | null>(null);
  const initialized = ref(false);
  const api = useApiClient();

  const accessToken = computed(() => accessTokenCookie.value || "");
  const refreshToken = computed(() => refreshTokenCookie.value || "");
  const loggedIn = computed(() => Boolean(accessTokenCookie.value));
  const fullName = computed(() => {
    if (!user.value) {
      return "";
    }
    return [user.value.first_name, user.value.last_name].filter(Boolean).join(" ") || user.value.username;
  });

  const applyLogin = (payload: LoginResponse) => {
    accessTokenCookie.value = payload.access;
    refreshTokenCookie.value = payload.refresh;
    user.value = payload.user;
  };

  const fetchProfile = async () => {
    user.value = await api.get<User>("/auth/profile/");
    return user.value;
  };

  const bootstrap = async () => {
    if (initialized.value) {
      return;
    }
    initialized.value = true;
    if (!loggedIn.value) {
      return;
    }
    try {
      await fetchProfile();
    } catch {
      logout();
    }
  };

  const login = async (payload: LoginPayload) => {
    const response = await api.post<LoginResponse>("/auth/login/", payload);
    applyLogin(response);
    return response.user;
  };

  const googleLogin = async (credential: string) => {
    const response = await api.post<LoginResponse>("/auth/google/", { credential });
    applyLogin(response);
    return response.user;
  };

  const register = async (payload: RegisterPayload) => {
    await api.post<User>("/auth/register/", payload);
    return login({ username: payload.username, password: payload.password });
  };

  const logout = () => {
    accessTokenCookie.value = null;
    refreshTokenCookie.value = null;
    user.value = null;
    useCartStore().clear();
    useFavoritesStore().clear();
  };

  return {
    accessToken,
    refreshToken,
    user,
    loggedIn,
    initialized,
    fullName,
    bootstrap,
    fetchProfile,
    login,
    googleLogin,
    register,
    logout
  };
});
