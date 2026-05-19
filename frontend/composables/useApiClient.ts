import type { FetchOptions } from "ofetch";
import { useAuthStore } from "~/stores/auth";

let refreshPromise: Promise<string> | null = null;

export const useApiClient = () => {
  const config = useRuntimeConfig();
  const auth = useAuthStore();

  const attemptTokenRefresh = async (): Promise<string> => {
    if (refreshPromise) {
      return refreshPromise;
    }
    refreshPromise = $fetch<{ access: string }>("/auth/refresh/", {
      baseURL: config.public.apiBase,
      method: "POST",
      body: { refresh: auth.refreshToken },
    })
      .then((response) => {
        auth.setAccessToken(response.access);
        return response.access;
      })
      .catch((error) => {
        auth.logout();
        throw error;
      })
      .finally(() => {
        refreshPromise = null;
      });
    return refreshPromise;
  };

  const request = async <T>(path: string, options: FetchOptions<"json"> = {}): Promise<T> => {
    const headers = new Headers(options.headers as HeadersInit | undefined);
    if (auth.accessToken) {
      headers.set("Authorization", `Bearer ${auth.accessToken}`);
    }
    try {
      return await $fetch<T>(path, {
        ...options,
        baseURL: config.public.apiBase,
        headers,
      });
    } catch (error: unknown) {
      const status = (error as { status?: number }).status
        ?? (error as { response?: { status?: number } }).response?.status;
      if (status === 401 && auth.refreshToken && path !== "/auth/refresh/") {
        const newAccessToken = await attemptTokenRefresh();
        headers.set("Authorization", `Bearer ${newAccessToken}`);
        return $fetch<T>(path, {
          ...options,
          baseURL: config.public.apiBase,
          headers,
        });
      }
      throw error;
    }
  };

  return {
    request,
    get: <T>(path: string, options: FetchOptions<"json"> = {}) => request<T>(path, { ...options, method: "GET" }),
    post: <T>(path: string, body?: unknown, options: FetchOptions<"json"> = {}) =>
      request<T>(path, { ...options, method: "POST", body }),
    patch: <T>(path: string, body?: unknown, options: FetchOptions<"json"> = {}) =>
      request<T>(path, { ...options, method: "PATCH", body }),
    put: <T>(path: string, body?: unknown, options: FetchOptions<"json"> = {}) =>
      request<T>(path, { ...options, method: "PUT", body }),
    delete: <T>(path: string, options: FetchOptions<"json"> = {}) => request<T>(path, { ...options, method: "DELETE" }),
  };
};
