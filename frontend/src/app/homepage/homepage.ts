import { Component, OnInit } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { HttpHeaders } from '@angular/common/http';
import { UserDetails } from '../services/user-details/user-details';


@Component({
  selector: 'app-homepage',
  imports: [RouterLink],
  templateUrl: './homepage.html',
  styleUrl: './homepage.css',
})
export class Homepage implements OnInit {
  constructor(private router: Router, private userDetails: UserDetails) {} 

  ngOnInit() {
    const token = localStorage.getItem('access_token'); 
    console.log("is token present?", !!token);
    if (!token) {
      this.router.navigate(['/login']);
    } else {
      const headers = new HttpHeaders({ Authorization: `Bearer ${token}` });
      this.userDetails.getUser({ headers }).subscribe({
        next: (res) => {
          console.log('User Details:', res);
          localStorage.setItem('user', JSON.stringify(res));
        },
        error: (err) => {
          console.error('Failed to fetch user details', err);
          this.logout();
        }
      });
    }
  }

  logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    this.router.navigate(['/login']);
  }

}
