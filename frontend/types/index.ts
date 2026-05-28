export interface Category {
  id: number;
  name: string;
  slug: string;
}

export interface Tag {
  id: number;
  name: string;
  slug: string;
}

export interface Seller {
  id: number;
  shop_name: string;
  description: string;
  avatar: string;
  created_at?: string;
  product_count?: number;
  average_rating?: number;
  products?: Product[];
}

export interface Product {
  id: number;
  name: string;
  slug: string;
  offer_group?: string;
  description?: string;
  price: string;
  old_price: string | null;
  discount_percent?: number;
  image_url: string;
  stock: number;
  category: Category;
  seller: Seller;
  tags: Tag[];
  average_rating: number;
  reviews_count: number;
  views_count: number;
  purchases_count: number;
  created_at: string;
  updated_at?: string;
  is_active?: boolean;
  is_favorite?: boolean;
  seller_offers?: ProductOffer[];
}

export interface ProductOffer {
  id: number;
  name: string;
  slug: string;
  offer_group?: string;
  price: string;
  old_price: string | null;
  discount_percent?: number;
  image_url: string;
  stock: number;
  seller: Seller;
  category: Category;
  average_rating: number;
  reviews_count: number;
}

export interface Review {
  id: number;
  user: {
    id: number;
    username: string;
  };
  rating: number;
  text: string;
  created_at: string;
}

export interface CartItem {
  id: number;
  quantity: number;
  subtotal: string;
  product: Product;
}

export interface Cart {
  id: number;
  created_at: string;
  updated_at: string;
  total_items: number;
  total_amount: string;
  items: CartItem[];
}

export interface OrderItem {
  id: number;
  quantity: number;
  price_at_purchase: string;
  subtotal: string;
  product: {
    id: number | null;
    name: string;
    image_url?: string;
  };
  seller: {
    id: number | null;
    shop_name: string;
  };
}

export interface Order {
  id: number;
  status: string;
  payment_method: "cash_on_delivery" | "card_on_delivery" | "card_online";
  total_amount: string;
  created_at: string;
  updated_at: string;
  items: OrderItem[];
  seller_total?: string;
}

export interface StripeCheckoutResponse {
  checkout_url: string;
}

export interface FavoriteItem {
  id: number;
  created_at: string;
  product: Product;
}

export interface User {
  id: number;
  username: string;
  email: string;
  role: "buyer" | "seller" | "admin";
  first_name: string;
  last_name: string;
  seller_profile?: Seller | null;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface RecommendationResponse {
  strategy: "personalized" | "popular_fallback";
  results: Product[];
}

export interface ProductListResponse {
  results: Product[];
}

export interface SellerDashboardResponse {
  product_count: number;
  orders_count: number;
  sales_count: number;
  total_sales: string;
  top_products: Product[];
  recent_orders: Array<{
    order_id: number;
    created_at: string;
    status: string;
    quantity: number;
    price_at_purchase: string;
    product: {
      id: number;
      name: string;
    };
  }>;
  chart_data: {
    labels: string[];
    revenue: number[];
    sales_count: number[];
  };
}

export interface ChatMessage {
  id: number;
  text: string;
  author: number;
  author_display: string;
  created_at: string;
  is_read: boolean;
}

export interface ChatRoom {
  id: number;
  order: number | null;
  buyer: number;
  seller: number;
  created_at: string;
  last_message: { text: string; created_at: string } | null;
  unread_count: number;
  other_party_name: string;
}
