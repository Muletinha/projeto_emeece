import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface Product {
  id: number;
  name: string;
  description?: string | null;
  price: number;
  stock_qty: number;
  image?: string | null;
}

export interface CartItemDto {
  id: number;
  product_id: number;
  product_name: string;
  unit_price: number;
  qty: number;
  max_qty: number;
  subtotal: number;
  image?: string | null;
}

export interface CartResponse {
  items: CartItemDto[];
  total: number;
}

const BASE = `${environment.apiUrl}/api`;

@Injectable({ providedIn: 'root' })
export class ApiService {
  constructor(private http: HttpClient) {}

  // produtos
  listProducts(): Observable<Product[]> {
    return this.http.get<Product[]>(`${BASE}/products`);
  }
  getProductById(id: number): Observable<Product> {
    return this.http.get<Product>(`${BASE}/products/${id}`);
  }
  getProduct(id: number): Observable<Product> { return this.getProductById(id); }

  upsertProduct(p: Partial<Product>) {
    return this.http.post<{ message: string }>(`${BASE}/products`, p);
  }
  createOrUpdateProduct(p: Partial<Product>) { return this.upsertProduct(p); }

  upload(file: File) {
    const form = new FormData();
    form.append('file', file);
    return this.http.post<{ filename: string }>(`${BASE}/upload`, form);
  }
  uploadImage(file: File) { return this.upload(file); }

  deleteProduct(id: number) {
    return this.http.delete<{ message: string }>(`${BASE}/products/${id}`);
  }

  //------------------------------------

  // carrinho
  addToCart(data: { cart_id?: string | null; product_id: number; qty: number }) {
    return this.http.post<{ message: string; cart_id: string }>(`${BASE}/cart/add`, data);
  }
  getCart(cartId: string): Observable<CartResponse> {
    return this.http.get<CartResponse>(`${BASE}/cart/${cartId}`);
  }
  updateCartItem(itemId: number, qty: number) {
    return this.http.put<{ message: string; item_id: number; cart_total: number }>(
      `${BASE}/cart/item/${itemId}`, { qty }
    );
  }
  deleteCartItem(itemId: number) {
    return this.http.delete<{ message: string }>(`${BASE}/cart/item/${itemId}`);
  }
  checkout(payload: { cart_id: string; shipping: 'padrao' | 'expresso' }) {
    return this.http.post<{ message: string; total_products: number; frete: number; total: number }>(
      `${BASE}/cart/checkout`, payload
    );
  }
}
