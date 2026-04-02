export default defineNuxtConfig({
  compatibilityDate: "2025-01-01",
  css: ["~/assets/css/main.css"],
  modules: ["@nuxtjs/tailwindcss", "@pinia/nuxt"],
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || "http://127.0.0.1:8000/api"
    }
  },
  app: {
    head: {
      title: "MarketFlow",
      meta: [
        {
          name: "viewport",
          content: "width=device-width, initial-scale=1"
        },
        {
          name: "description",
          content: "Маркетплейс MVP с персональными рекомендациями товаров, интерфейсом на русском и ценами в тенге."
        }
      ],
      link: [
        {
          rel: "preconnect",
          href: "https://fonts.googleapis.com"
        },
        {
          rel: "preconnect",
          href: "https://fonts.gstatic.com",
          crossorigin: ""
        },
        {
          rel: "stylesheet",
          href: "https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;700&display=swap"
        }
      ]
    }
  },
  devtools: {
    enabled: false
  }
});
