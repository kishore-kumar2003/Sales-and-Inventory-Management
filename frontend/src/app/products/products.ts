import { Component, OnInit, ViewChild } from '@angular/core';
import { ProductsService } from '../services/product/products-service';
import { CommonModule } from '@angular/common';
import { NgForm, FormsModule } from '@angular/forms';
declare var bootstrap: any;

export interface Product {
  id: number;
  name: string;
  description: string;
  cost_price: string;
  selling_price: string;
  minimum_stock: number;
  current_stock: number;
  low_stock_alert: boolean;
  profit_margin: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

@Component({
  selector: 'app-products',
  imports: [CommonModule, FormsModule],
  templateUrl: './products.html',
  styleUrl: './products.css',
})


export class Products implements OnInit {

  @ViewChild('addProductForm') addProductForm!: NgForm;
  @ViewChild('editProductForm') editProductForm!: NgForm;

  profitMargin: number = 0;
  products_details: Product[] = [];
  Edit_product_id: number | null = null;
  Edit_product_details = {
    name: '',
    description: '',
    cost_price: '',
    selling_price: '',
    minimum_stock: 0,
    current_stock: 0,
    low_stock_alert: false,
    profit_margin: 0,
    is_active: false,
    updated_at: '',
  }
  newProduct = {
    cost_price: 0,
    selling_price: 0,
  }

  constructor(private productsService: ProductsService) {}

  ngOnInit(): void {
    this.productsService.getProducts().subscribe({
      next: (res) => {
        this.products_details = res;
        console.log('Products:', this.products_details);
      },
      error: (err) => {
        console.error('Failed to fetch products', err);
      }
    });
  }

  addProduct() {
    console.log('Add product'); 
    const modalElement = document.getElementById('addProductDialog');
    const modalAddProduct = new bootstrap.Modal(modalElement);
    modalAddProduct.show();
  }


  calculateProfitMargin(cost_price: number, selling_price: number) {
    console.log('cost price:', cost_price, 'selling price:', selling_price);

    if (selling_price !== 0) {
      this.profitMargin = parseFloat(
        (((selling_price - cost_price) / selling_price) * 100).toFixed(2)
      );
    } else {
      this.profitMargin = 0;
    }
  }


  addNewProduct() {
    console.log('Add new product', this.addProductForm.value);
    const newProduct = {
      name: this.addProductForm.value.name,
      description: this.addProductForm.value.description,
      cost_price: this.addProductForm.value.cost_price,
      selling_price: this.addProductForm.value.selling_price,
      minimum_stock: this.addProductForm.value.minimum_stock,
      current_stock: this.addProductForm.value.current_stock,
      low_stock_alert: this.addProductForm.value.low_stock_alert,
      profit_margin: this.calculateProfitMargin(this.addProductForm.value.cost_price, this.addProductForm.value.selling_price),
      is_active: this.addProductForm.value.is_active,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    this.productsService.addproduct(newProduct).subscribe({
      next: (res) => {
        console.log('Product added successfully', res);
        this.products_details.push(res);
        this.addCloseDialog();
      },
      error: (err) => {
        console.error('Failed to add product', err);
      }
    });
  }


  editProduct(id: number) {
    console.log('Edit product with ID:', id);
    this.Edit_product_id = this.products_details.find(product => product.id === id)?.id || null;
    const product = this.products_details.find(product => product.id === id);
    if (product) {
      this.Edit_product_details.name = product.name;
      this.Edit_product_details.description = product.description;
      this.Edit_product_details.cost_price = product.cost_price;
      this.Edit_product_details.selling_price = product.selling_price;
      this.Edit_product_details.minimum_stock = product.minimum_stock;
      this.Edit_product_details.current_stock = product.current_stock;
      this.Edit_product_details.low_stock_alert = product.low_stock_alert;
      this.Edit_product_details.profit_margin = product.profit_margin;
      this.Edit_product_details.is_active = product.is_active;
      this.Edit_product_details.updated_at = product.updated_at;
    }

  const modalElement = document.getElementById('editProductDialog');
  const modalEditProduct = new bootstrap.Modal(modalElement);
  modalEditProduct.show();
  }

  updateProduct() {
    console.log('Update product with ID:', this.Edit_product_id);
    this.Edit_product_details.updated_at = new Date().toISOString();
    this.productsService.updateProduct(Number(this.Edit_product_id), this.Edit_product_details).subscribe({
      next: (res) => {
        console.log('Product updated successfully', res);
        const index = this.products_details.findIndex(product => product.id === this.Edit_product_id);
        if (index !== -1) {
          this.products_details[index] = res;
        }
        this.editCloseDialog();
      },
      error: (err) => {
        console.error('Failed to update product', err);
      }
    });
  }

  deleteProduct(id: number) {
    console.log('Delete product with ID:', id);
    this.productsService.deleteProduct(id).subscribe({
      next: (res) => {
        console.log('Product deleted successfully', res);
        this.products_details = this.products_details.filter(product => product.id !== id);
      },
      error: (err) => {
        console.error('Failed to delete product', err);
      }
    }); 
  }

  addCloseDialog() {
    this.addProductForm.resetForm();
    const modalElement = document.getElementById('addProductDialog');
    const modalAddProduct = bootstrap.Modal.getInstance(modalElement);
    modalAddProduct.hide();
  }

  editCloseDialog() {
    this.editProductForm.resetForm();
    const modalElement = document.getElementById('editProductDialog');
    const modalEditProduct = bootstrap.Modal.getInstance(modalElement);
    modalEditProduct.hide();
  }

}
