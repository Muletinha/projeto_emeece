export interface CartItem {
  id: number;
  product_id: number;
  product_name: string;
  unit_price: number;
  qty: number;
  max_qty: number;
  subtotal: number;
}

export interface CartResponse {
  items: CartItem[];
  total: number;
}
