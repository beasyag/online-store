type ApiErrorPayload =
  | string
  | {
      detail?: string;
      [key: string]: unknown;
    };

const normalizeMessage = (value: unknown): string | null => {
  if (!value) {
    return null;
  }

  if (typeof value === "string") {
    return value;
  }

  if (Array.isArray(value)) {
    const messages = value.map((item) => normalizeMessage(item)).filter(Boolean);
    return messages.length ? messages.join(" ") : null;
  }

  if (typeof value === "object") {
    const record = value as Record<string, unknown>;
    if (typeof record.detail === "string" && record.detail.trim()) {
      return record.detail;
    }

    const fieldMessages = Object.entries(record)
      .map(([field, fieldValue]) => {
        const message = normalizeMessage(fieldValue);
        if (!message) {
          return null;
        }
        return field === "non_field_errors" ? message : `${field}: ${message}`;
      })
      .filter(Boolean);

    return fieldMessages.length ? fieldMessages.join(" ") : null;
  }

  return null;
};

export const useApiError = () => {
  const getErrorMessage = (error: { data?: ApiErrorPayload; message?: string } | null | undefined, fallback: string) => {
    return normalizeMessage(error?.data) || normalizeMessage(error?.message) || fallback;
  };

  return {
    getErrorMessage
  };
};
