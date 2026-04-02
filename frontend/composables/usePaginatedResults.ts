import type { PaginatedResponse } from "~/types";

export const usePaginatedResults = <T>(payload: PaginatedResponse<T> | T[] | null | undefined) => {
  if (!payload) {
    return [];
  }
  return Array.isArray(payload) ? payload : payload.results;
};

