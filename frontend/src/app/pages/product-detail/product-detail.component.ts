import { Component, OnInit, Inject } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PLATFORM_ID } from '@angular/core';

@Component({
  selector: 'app-product-detail',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './product-detail.component.html'
})
export class ProductDetailComponent implements OnInit {
  product: any = null;
  qty = 1;
  cartId: string | null = null;

  constructor(
    private route: ActivatedRoute,
    private api: ApiService,
    @Inject(PLATFORM_ID) private platformId: Object
  ) {}

  isBrowser() { return isPlatformBrowser(this.platformId); }

  ngOnInit() {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.api.getProduct(id).subscribe(p => {
      this.product = p;
      if (this.product?.stock_qty <= 0) this.qty = 0;
    }, _ => this.product = null);

    if (this.isBrowser()) this.cartId = localStorage.getItem('cart_id');
  }

  get outOfStock() {
    return !this.product || this.product.stock_qty <= 0;
  }

  onQtyInputChange() {
    if (!this.product) return;
    const max = Number(this.product.stock_qty || 0);
    this.qty = Math.max(1, Math.min(Number(this.qty || 1), max));
  }

  incDetail() {
    if (!this.product) return;
    if ((+this.qty || 1) < this.product.stock_qty) {
      this.qty = (+this.qty || 1) + 1;
    }
    this.onQtyInputChange();
  }

  decDetail() {
    if ((+this.qty || 1) > 1) {
      this.qty = (+this.qty || 1) - 1;
    }
    this.onQtyInputChange();
  }

  addToCart() {
    if (this.outOfStock || !this.product) return;
    const max = Number(this.product.stock_qty || 0);
    const desired = Number(this.qty || 1);

    if (desired > max) {
      alert(`Quantidade solicitada (${desired}) acima do estoque disponível (${max}).`);
      this.qty = max;
      return;
    }
    if (desired < 1) {
      alert('Quantidade mínima é 1.');
      this.qty = 1;
      return;
    }

    const payload = { cart_id: this.cartId, product_id: this.product.id, qty: desired };
    this.api.addToCart(payload).subscribe({
      next: (r: any) => {
        if (this.isBrowser() && r.cart_id) localStorage.setItem('cart_id', r.cart_id);
        alert('Adicionado ao carrinho!');
      },
      error: err => alert(err?.error?.error || 'Erro ao adicionar')
    });
  }
}
