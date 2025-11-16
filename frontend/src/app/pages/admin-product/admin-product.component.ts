import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService, Product } from '../../services/api.service';
import { environment } from '../../../environments/environment';

type AdminProductModel = {
  id: number | null;
  name: string;
  description?: string | null;
  price: number | null;
  stock_qty: number | null;
  image?: string | null;
};

@Component({
  selector: 'app-admin-product',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './admin-product.component.html'
})
export class AdminProductComponent implements OnInit {
  model: AdminProductModel = {
    id: null,
    name: '',
    description: '',
    price: null,
    stock_qty: null,
    image: null
  };

  // se o produto existe habilita a imagem e permite excluir
  exists = false;
  // URL base para o servidor FLASK
  imageBaseUrl = `${environment.apiUrl}/uploads/`;
  // nome do arquivo
  uploadedFileName: string | null = null;

  constructor(private api: ApiService) {}

  ngOnInit(): void {}

  // quando o ID muda
  onIdChanged() {
    const id = Number(this.model.id);
    if (!id || isNaN(id)) {
      this.exists = false;
      this.clearExceptId();
      return;
    }

    this.api.getProduct(id).subscribe({
      next: (p: Product) => {
        // se produto existe popula o banco e permite o excluir
        this.exists = true;
        this.model = {
          id: p.id,
          name: p.name,
          description: p.description ?? '',
          price: p.price,
          stock_qty: p.stock_qty,
          image: p.image ?? null
        };
        this.uploadedFileName = null;
      },
      error: _ => {
        // caso não exista mantem o ID, limpa campos e não permite excluir
        this.exists = false;
        this.clearExceptId();
      }
    });
  }

  clearExceptId() {
    const id = this.model.id;
    this.model = {
      id,
      name: '',
      description: '',
      price: null,
      stock_qty: null,
      image: null
    };
    this.uploadedFileName = null;
  }

  // upload da imagem, salva no servidor e grava em models
  async onFileSelected(evt: Event) {
    const input = evt.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) return;
    const file = input.files[0];

    try {
      const r = await this.api.uploadImage(file).toPromise();
      if (r && r.filename) {
        this.model.image = r.filename;
        this.uploadedFileName = r.filename;
      }
    } catch (e) {
      alert('Erro ao enviar imagem.');
    }
  }

  // salva (cria e atualiza)
  save() {
    const payload: Partial<Product> = {
      id: Number(this.model.id),
      name: (this.model.name ?? '').trim(),
      description: this.model.description ?? '',
      price: Number(this.model.price ?? 0),
      stock_qty: Number(this.model.stock_qty ?? 0),
      image: this.model.image ?? undefined
    };

    if (!payload.id || !payload.name || isNaN(payload.price!) || isNaN(payload.stock_qty!)) {
      alert('Preencha ID, Nome, Preço e Estoque corretamente.');
      return;
    }

    this.api.createOrUpdateProduct(payload).subscribe({
      next: _ => {
        alert('Produto salvo com sucesso.');
        this.exists = true; // começa a existir depois que salva
      },
      error: _ => alert('Erro ao salvar produto.')
    });
  }

  // permite excluir somente se existe
  remove() {
    if (!this.exists || !this.model.id) return;
    if (!confirm('Tem certeza que deseja excluir este produto?')) return;

    this.api.deleteProduct(this.model.id).subscribe({
      next: _ => {
        alert('Produto excluído.');
        this.exists = false;
        this.clearExceptId();
      },
      error: _ => alert('Erro ao excluir produto.')
    });
  }

  // URL completa da imagem para o preview
  get imageUrl(): string | null {
    return this.model.image ? `${this.imageBaseUrl}${this.model.image}` : null;
  }
}
