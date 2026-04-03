import { useAuthStore } from "~/stores/auth";
import { useCartStore } from "~/stores/cart";

export default defineNuxtPlugin(async () => {
  const auth = useAuthStore();
  await auth.bootstrap();

  if (auth.loggedIn) {
    const cartStore = useCartStore();
    await Promise.allSettled([cartStore.fetchCart()]);
  }
});
