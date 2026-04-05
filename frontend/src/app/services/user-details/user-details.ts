import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class UserDetails {
  private apiURL = 'http://localhost:8000/api/accounts';

  constructor(private http: HttpClient) {}

  getUser(options: { headers?: any } = {}): Observable<any> {
    return this.http.get(`${this.apiURL}/profile/`, options);
  }

  getUsers(data: any): Observable<any> {
    return this.http.get(`${this.apiURL}/profile/`, data);
  }

  updateUser(data: any): Observable<any> {
    return this.http.put(`${this.apiURL}/profile/`, data);
  }

  deleteUser(data: any): Observable<any> {
    return this.http.delete(`${this.apiURL}/profile/`, data);
  }

  register(data: any): Observable<any> {
    return this.http.post(`${this.apiURL}/register/`, data);
  }
}
