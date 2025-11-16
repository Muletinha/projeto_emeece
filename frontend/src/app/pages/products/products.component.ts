import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-products',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './products.component.html'
})
export class ProductsComponent implements OnInit {
  products: any[] = [];
  constructor(private api: ApiService, private router: Router) {}
  ngOnInit() { this.load(); }
  load() {
    this.api.listProducts().subscribe((r:any) => this.products = r);
  }
  openDetail(p:any) {
    this.router.navigate(['/product', p.id]);
  }
}
