import type { FavoriteItem, PaginatedResponse } from "~/types";
import { useApiClient } from "~/composables/useApiClient";
import { useAuthStore } from "~/stores/auth";

export const useFavoritesStore = defineStore("favorites", () => {
  const api = useApiClient();
  const auth = useAuthStore();
  const items = ref<FavoriteItem[]>([]);

  const ids = computed(() => new Set(items.value.map((item) => item.product.id)));

  const fetchFavorites = async () => {
    if (!auth.loggedIn) {
      items.value = [];
      return items.value;
    }
    const response = await api.get<PaginatedResponse<FavoriteItem>>("/favorites/");
    items.value = response.results;
    return items.value;
  };

  const toggleFavorite = async (productId: number) => {
    const response = await api.post<{ status: "added" | "removed" }>("/favorites/toggle/", {
      product_id: productId
    });
    if (response.status === "removed") {
      items.value = items.value.filter((item) => item.product.id !== productId);
    } else {
      await fetchFavorites();
    }
    return response.status;
  };

  const clear = () => {
    items.value = [];
  };

  return {
    items,
    ids,
    fetchFavorites,
    toggleFavorite,
    clear
  };
});
