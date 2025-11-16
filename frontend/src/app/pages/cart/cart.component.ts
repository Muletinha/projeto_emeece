import { Component, OnInit, Inject } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PLATFORM_ID } from '@angular/core';
import { ApiService, CartResponse } from '../../services/api.service';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-cart',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './cart.component.html'
})
export class CartComponent implements OnInit {
  cartId: string | null = null;
  items: CartResponse['items'] = [];
  productsTotal = 0;
  shippingType: 'padrao' | 'expresso' = 'padrao';
  shippingValues: Record<'padrao' | 'expresso', number> = { padrao: 10, expresso: 25 };
  imageBaseUrl = `${environment.apiUrl}/uploads/`;

  constructor(private api: ApiService, @Inject(PLATFORM_ID) private platformId: Object) {}

  ngOnInit() {
    if (this.isBrowser()) this.cartId = localStorage.getItem('cart_id');
    if (this.cartId) this.load();
  }

  isBrowser() { return isPlatformBrowser(this.platformId); }

  load() {
    if (!this.cartId) return;
    this.api.getCart(this.cartId).subscribe(r => {
      this.items = r.items;
      this.productsTotal = r.total || 0;
    });
  }

  // botoes + e - funcionais no carrinho
  incCart(it: any) {
    if ((+it.qty || 1) < it.max_qty) {
      it.qty = (+it.qty || 1) + 1;
      this.onQtyChange(it);
    } else {
      alert(`Máximo disponível: ${it.max_qty}`);
    }
  }
  decCart(it: any) {
    if ((+it.qty || 1) > 1) {
      it.qty = (+it.qty || 1) - 1;
      this.onQtyChange(it);
    }
  }

  onQtyChange(it: any) {
    const clamped = Math.max(1, Math.min(Number(it.qty || 1), Number(it.max_qty || 1)));
    if (clamped !== it.qty) {
      it.qty = clamped;
      alert(`Quantidade ajustada para ${clamped} (máx: ${it.max_qty}).`);
    }
    this.api.updateCartItem(it.id, it.qty).subscribe({
      next: () => this.load(),
      error: err => {
        const msg = err?.error?.error || 'Erro ao atualizar quantidade';
        alert(msg);
        this.load();
      }
    });
  }

  removeItem(id: number) {
    this.api.deleteCartItem(id).subscribe(_ => this.load());
  }

  checkout() {
    if (!this.cartId) return;
    this.api.checkout({ cart_id: this.cartId, shipping: this.shippingType }).subscribe({
      next: r => {
        alert(`Pedido finalizado.\nProdutos: R$ ${r.total_products.toFixed(2)}\nFrete: R$ ${r.frete.toFixed(2)}\nTotal: R$ ${r.total.toFixed(2)}`);
        if (this.isBrowser()) localStorage.removeItem('cart_id');
        this.cartId = null;
        this.items = [];
        this.productsTotal = 0;
      },
      error: err => alert('Erro no checkout: ' + (err.error?.error || ''))
    });
  }

  getTotal() {
    return this.productsTotal + (this.shippingValues[this.shippingType] || 0);
  }
}
