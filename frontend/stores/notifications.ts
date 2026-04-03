export type NotificationTone = "error" | "success";

export interface NotificationItem {
  id: number;
  message: string;
  tone: NotificationTone;
}

export const useNotificationsStore = defineStore("notifications", () => {
  const items = ref<NotificationItem[]>([]);
  let nextId = 1;

  const push = (message: string, tone: NotificationTone = "error") => {
    const id = nextId++;
    items.value.push({ id, message, tone });

    setTimeout(() => {
      remove(id);
    }, 5000);
  };

  const remove = (id: number) => {
    items.value = items.value.filter((item) => item.id !== id);
  };

  const error = (message: string) => push(message, "error");
  const success = (message: string) => push(message, "success");

  return {
    items,
    push,
    remove,
    error,
    success
  };
});
