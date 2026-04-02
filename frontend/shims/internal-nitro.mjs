const runtimeConfig = Object.freeze({
  app: {
    baseURL: process.env.NUXT_APP_BASE_URL || "/",
    buildAssetsDir: process.env.NUXT_APP_BUILD_ASSETS_DIR || "/_nuxt/",
    cdnURL: process.env.NUXT_APP_CDN_URL || ""
  },
  public: {
    apiBase: process.env.NUXT_PUBLIC_API_BASE || "http://127.0.0.1:8000/api"
  }
});

const appConfig = Object.freeze({
  nuxt: {
    buildId: process.env.NUXT_BUILD_ID || "dev"
  }
});

export function useRuntimeConfig() {
  return runtimeConfig;
}

export function useAppConfig() {
  return appConfig;
}

export default runtimeConfig;
