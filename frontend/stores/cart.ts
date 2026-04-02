import type { Cart } from "~/types";
import { useApiClient } from "~/composables/useApiClient";
import { useAuthStore } from "~/stores/auth";

export const useCartStore = defineStore("cart", () => {
  const api = useApiClient();
  const auth = useAuthStore();
  const cart = ref<Cart | null>(null);
  const pending = ref(false);

  const count = computed(() => cart.value?.total_items ?? 0);
  const totalAmount = computed(() => cart.value?.total_amount ?? "0.00");

  const fetchCart = async () => {
    if (!auth.loggedIn) {
      cart.value = null;
      return null;
    }
    pending.value = true;
    try {
      cart.value = await api.get<Cart>("/cart/");
      return cart.value;
    } finally {
      pending.value = false;
    }
  };

  const addToCart = async (productId: number, quantity = 1) => {
    cart.value = await api.post<Cart>("/cart/add/", {
      product_id: productId,
      quantity
    });
    return cart.value;
  };

  const updateItem = async (itemId: number, quantity: number) => {
    cart.value = await api.patch<Cart>(`/cart/item/${itemId}/`, { quantity });
    return cart.value;
  };

  const removeItem = async (itemId: number) => {
    cart.value = await api.delete<Cart>(`/cart/item/${itemId}/`);
    return cart.value;
  };

  const clear = () => {
    cart.value = null;
  };

  return {
    cart,
    pending,
    count,
    totalAmount,
    fetchCart,
    addToCart,
    updateItem,
    removeItem,
    clear
  };
});
