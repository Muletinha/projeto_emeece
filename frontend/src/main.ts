import { bootstrapApplication } from '@angular/platform-browser';
import { ApplicationConfig } from '@angular/core';
import { provideRouter, Routes } from '@angular/router';
import { provideHttpClient, withFetch } from '@angular/common/http';
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterOutlet } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: 'products', pathMatch: 'full' },
  { path: 'products', loadComponent: () => import('./app/pages/products/products.component').then(m => m.ProductsComponent) },
  { path: 'product/:id', loadComponent: () => import('./app/pages/product-detail/product-detail.component').then(m => m.ProductDetailComponent) },
  { path: 'admin', loadComponent: () => import('./app/pages/admin-product/admin-product.component').then(m => m.AdminProductComponent) },
  { path: 'cart', loadComponent: () => import('./app/pages/cart/cart.component').then(m => m.CartComponent) },
  { path: '**', redirectTo: 'products' }
];

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterOutlet],
  template: `
    <nav class="topbar">
      <a routerLink="/cart" class="carticon">🛒</a>
      <a routerLink="/products" class="producticon">EMEECE - Smart Gym</a>
      <a routerLink="/admin" class="adminicon">Gerenciar Produtos</a>
    </nav>
    <router-outlet></router-outlet>
  `
})
class AppComponent {}

const appConfig: ApplicationConfig = {
  providers: [provideHttpClient(withFetch()), provideRouter(routes)]
};

bootstrapApplication(AppComponent, appConfig).catch(console.error);
