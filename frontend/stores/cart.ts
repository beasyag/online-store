import type { Cart } from "~/types";
import { useApiError } from "~/composables/useApiError";
import { useApiClient } from "~/composables/useApiClient";
import { useAuthStore } from "~/stores/auth";
import { useNotificationsStore } from "~/stores/notifications";

export const useCartStore = defineStore("cart", () => {
  const api = useApiClient();
  const auth = useAuthStore();
  const notifications = useNotificationsStore();
  const { getErrorMessage } = useApiError();
  const cart = ref<Cart | null>(null);
  const pending = ref(false);
  const errorMessage = ref("");

  const count = computed(() => cart.value?.total_items ?? 0);
  const totalAmount = computed(() => cart.value?.total_amount ?? "0.00");

  const fetchCart = async () => {
    if (!auth.loggedIn) {
      cart.value = null;
      return null;
    }
    pending.value = true;
    errorMessage.value = "";
    try {
      cart.value = await api.get<Cart>("/cart/");
      return cart.value;
    } catch (error: any) {
      errorMessage.value = getErrorMessage(error, "Не удалось загрузить корзину.");
      throw error;
    } finally {
      pending.value = false;
    }
  };

  const addToCart = async (productId: number, quantity = 1) => {
    errorMessage.value = "";
    try {
      cart.value = await api.post<Cart>("/cart/add/", {
        product_id: productId,
        quantity
      });
      notifications.success("Товар добавлен в корзину.");
      return cart.value;
    } catch (error: any) {
      errorMessage.value = getErrorMessage(error, "Не удалось добавить товар в корзину.");
      notifications.error(errorMessage.value);
      throw error;
    }
  };

  const updateItem = async (itemId: number, quantity: number) => {
    errorMessage.value = "";
    try {
      cart.value = await api.patch<Cart>(`/cart/item/${itemId}/`, { quantity });
      notifications.success("Корзина обновлена.");
      return cart.value;
    } catch (error: any) {
      errorMessage.value = getErrorMessage(error, "Не удалось обновить количество товара.");
      notifications.error(errorMessage.value);
      throw error;
    }
  };

  const removeItem = async (itemId: number) => {
    errorMessage.value = "";
    try {
      cart.value = await api.delete<Cart>(`/cart/item/${itemId}/`);
      notifications.success("Товар удалён из корзины.");
      return cart.value;
    } catch (error: any) {
      errorMessage.value = getErrorMessage(error, "Не удалось удалить товар из корзины.");
      notifications.error(errorMessage.value);
      throw error;
    }
  };

  const clear = () => {
    cart.value = null;
    errorMessage.value = "";
  };

  return {
    cart,
    pending,
    errorMessage,
    count,
    totalAmount,
    fetchCart,
    addToCart,
    updateItem,
    removeItem,
    clear
  };
});
