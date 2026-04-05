import { Routes } from '@angular/router';
import { LoginComponent } from './login/login';
import { Homepage } from './homepage/homepage';
import { Products } from './products/products';

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' }, // correct literal 'full'
  { path: 'login', component: LoginComponent },
  { path: 'homepage', component: Homepage },
  { path: 'products', component: Products}
];