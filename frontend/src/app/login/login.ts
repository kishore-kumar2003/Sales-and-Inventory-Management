import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../services/auth';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.html',
  styleUrls: ['./login.css']
})
export class LoginComponent {
  email = '';
  password = '';

  constructor(private auth: AuthService, private router: Router) {}

  login() {
    const body = { email: this.email, password: this.password };
    this.auth.login(body).subscribe({
        next: (res) => {
        localStorage.setItem('access_token', res.access);
        localStorage.setItem('refresh_token', res.refresh);
        this.router.navigate(['/homepage']);
      },
      error: (err) => {
        console.error('Login Failed', err);
      }
    });
  }
}