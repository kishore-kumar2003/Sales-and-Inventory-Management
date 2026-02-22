import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiURL = 'http://localhost:8000/api'; // Django API

  constructor(private http: HttpClient) {}

  login(body: { email: string; password: string }): Observable<any> {
    return this.http.post(`${this.apiURL}/login/`, body);
  }

  register(data: any): Observable<any> {
    return this.http.post(`${this.apiURL}/register/`, data);
  }
}