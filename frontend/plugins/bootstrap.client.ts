import { useAuthStore } from "~/stores/auth";
import { useCartStore } from "~/stores/cart";
import { useFavoritesStore } from "~/stores/favorites";

export default defineNuxtPlugin(async () => {
  const auth = useAuthStore();
  await auth.bootstrap();

  if (auth.loggedIn) {
    const cartStore = useCartStore();
    const favoritesStore = useFavoritesStore();
    await Promise.allSettled([cartStore.fetchCart(), favoritesStore.fetchFavorites()]);
  }
});
