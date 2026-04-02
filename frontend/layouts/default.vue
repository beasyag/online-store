<template>
  <div class="min-h-screen">
    <AppHeader />
    <main class="pb-16 pt-6 sm:pb-20 sm:pt-8">
      <slot />
    </main>
    <footer class="border-t border-white/60 py-8">
      <div class="shell flex flex-col gap-2 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between">
        <p>MarketFlow MVP на Nuxt 3 и Django REST Framework.</p>
        <p>Персональные рекомендации, multi-vendor заказы и кабинет продавца.</p>
      </div>
    </footer>
  </div>
</template>
