export const useFormatters = () => {
  const categoryNames: Record<string, string> = {
    Electronics: "Электроника",
    Clothing: "Одежда",
    Shoes: "Обувь",
    Accessories: "Аксессуары",
    Home: "Товары для дома",
    Beauty: "Красота",
    Sports: "Спорт",
    Books: "Книги"
  };

  const tagNames: Record<string, string> = {
    wireless: "беспроводной",
    gaming: "игровой",
    office: "для офиса",
    premium: "премиум",
    portable: "портативный",
    smart: "умный",
    "usb-c": "usb-c",
    bluetooth: "bluetooth",
    cotton: "хлопок",
    casual: "повседневный",
    oversize: "оверсайз",
    winter: "зима",
    summer: "лето",
    minimal: "минимализм",
    daily: "на каждый день",
    classic: "классика",
    sport: "спорт",
    leather: "кожа",
    running: "для бега",
    lightweight: "легкий",
    outdoor: "для улицы",
    compact: "компактный",
    travel: "для поездок",
    gift: "подарок",
    unisex: "унисекс",
    cozy: "уют",
    kitchen: "кухня",
    storage: "хранение",
    decor: "декор",
    family: "для семьи",
    eco: "эко",
    hydration: "увлажнение",
    sensitive: "для чувствительной кожи",
    organic: "натуральный",
    care: "уход",
    fitness: "фитнес",
    "home-workout": "домашние тренировки",
    pro: "pro",
    bestseller: "бестселлер",
    learning: "обучение",
    fiction: "художественная литература",
    "non-fiction": "нон-фикшн",
    "new-release": "новинка",
    popular: "популярное",
    apple: "apple",
    iphone: "iphone",
    samsung: "samsung",
    android: "android",
    audio: "аудио",
    console: "консоль",
    lego: "lego",
    toy: "игрушка",
    kids: "для детей",
    barbie: "barbie",
    car: "машинка",
    soft: "мягкая игрушка",
    fashion: "мода",
    shoes: "обувь",
    nike: "nike",
    adidas: "adidas",
    xiaomi: "xiaomi",
    "home-gadget": "техника для дома",
    cleaning: "уборка",
    skincare: "уход за кожей",
    perfume: "парфюм",
    books: "книги",
    programming: "программирование"
  };

  const orderStatuses: Record<string, string> = {
    pending: "Ожидает",
    paid: "Оплачен",
    processing: "В обработке",
    shipped: "В пути",
    completed: "Завершен",
    canceled: "Отменен"
  };

  const formatMoney = (value?: string | number | null) => {
    const amount = Number(value || 0);
    return new Intl.NumberFormat("ru-KZ", {
      style: "currency",
      currency: "KZT",
      maximumFractionDigits: 0
    }).format(amount);
  };

  const formatDate = (value?: string | null) => {
    if (!value) {
      return "";
    }
    return new Intl.DateTimeFormat("ru-KZ", {
      dateStyle: "medium"
    }).format(new Date(value));
  };

  const formatRating = (value?: number | null) => Number(value || 0).toFixed(1);
  const formatCategoryName = (value?: string | null) => (value ? categoryNames[value] || value : "");
  const formatTagName = (value?: string | null) => (value ? tagNames[value] || value : "");
  const formatOrderStatus = (value?: string | null) => (value ? orderStatuses[value] || value : "");
  const formatPaymentMethod = (value?: string | null) => {
    const paymentMethods: Record<string, string> = {
      cash_on_delivery: "Наличными при получении",
      card_on_delivery: "Картой при получении",
      card_online: "Онлайн картой"
    };
    return value ? paymentMethods[value] || value : "";
  };
  const formatOrderStatusHint = (value?: string | null) => {
    const hints: Record<string, string> = {
      pending: "Заказ создан и ожидает подтверждения.",
      paid: "Оплата получена, заказ передан в обработку.",
      processing: "Продавец комплектует и подтверждает позиции.",
      shipped: "Заказ передан в доставку.",
      completed: "Заказ завершён и доставлен.",
      canceled: "Заказ отменён."
    };
    return value ? hints[value] || "" : "";
  };

  return {
    formatMoney,
    formatDate,
    formatRating,
    formatCategoryName,
    formatTagName,
    formatOrderStatus,
    formatOrderStatusHint,
    formatPaymentMethod
  };
};
