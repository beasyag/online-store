import type { FetchOptions } from "ofetch";
import { useAuthStore } from "~/stores/auth";

export const useApiClient = () => {
  const config = useRuntimeConfig();
  const auth = useAuthStore();

  const request = <T>(path: string, options: FetchOptions<"json"> = {}) => {
    const headers = new Headers(options.headers as HeadersInit | undefined);
    if (auth.accessToken) {
      headers.set("Authorization", `Bearer ${auth.accessToken}`);
    }
    return $fetch<T>(path, {
      ...options,
      baseURL: config.public.apiBase,
      headers
    });
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
    delete: <T>(path: string, options: FetchOptions<"json"> = {}) => request<T>(path, { ...options, method: "DELETE" })
  };
};
