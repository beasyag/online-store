import type { FavoriteItem, PaginatedResponse } from "~/types";
import { useApiError } from "~/composables/useApiError";
import { useApiClient } from "~/composables/useApiClient";
import { useAuthStore } from "~/stores/auth";
import { useNotificationsStore } from "~/stores/notifications";

export const useFavoritesStore = defineStore("favorites", () => {
  const api = useApiClient();
  const auth = useAuthStore();
  const notifications = useNotificationsStore();
  const { getErrorMessage } = useApiError();
  const items = ref<FavoriteItem[]>([]);
  const errorMessage = ref("");

  const ids = computed(() => new Set(items.value.map((item) => item.product.id)));

  const fetchFavorites = async () => {
    if (!auth.loggedIn) {
      items.value = [];
      return items.value;
    }
    errorMessage.value = "";
    try {
      const response = await api.get<PaginatedResponse<FavoriteItem>>("/favorites/");
      items.value = response.results;
      return items.value;
    } catch (error: any) {
      errorMessage.value = getErrorMessage(error, "Не удалось загрузить избранное.");
      throw error;
    }
  };

  const toggleFavorite = async (productId: number) => {
    errorMessage.value = "";
    try {
      const response = await api.post<{ status: "added" | "removed" }>("/favorites/toggle/", {
        product_id: productId
      });
      if (response.status === "removed") {
        items.value = items.value.filter((item) => item.product.id !== productId);
        notifications.success("Товар удалён из избранного.");
      } else {
        await fetchFavorites();
        notifications.success("Товар добавлен в избранное.");
      }
      return response.status;
    } catch (error: any) {
      errorMessage.value = getErrorMessage(error, "Не удалось обновить избранное.");
      notifications.error(errorMessage.value);
      throw error;
    }
  };

  const clear = () => {
    items.value = [];
    errorMessage.value = "";
  };

  return {
    items,
    ids,
    errorMessage,
    fetchFavorites,
    toggleFavorite,
    clear
  };
});
