import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';


@Injectable({
  providedIn: 'root',
})

export class ProductsService {
    
  private apiURL = 'http://localhost:8000/api/core';

  constructor(private http: HttpClient) {}

  getProducts(): Observable<any> {
    return this.http.get(`${this.apiURL}/products/`);
  }

  getProduct(): Observable<any> {
    return this.http.get(`${this.apiURL}/products/<id>/`);
  }

  addproduct(data: any): Observable<any> {
    return this.http.post(`${this.apiURL}/products/`, data);
  }

  updateProduct(id: number, data: any): Observable<any> {
    return this.http.put(`${this.apiURL}/products/${id}/`, data);
  }

  deleteProduct(id: any): Observable<any> {
    return this.http.delete(`${this.apiURL}/products/${id}/`, id);
  }

}
