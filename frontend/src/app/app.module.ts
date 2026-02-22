import { inject } from '@angular/core';
import { HttpRequest, HttpHandlerFn, HttpInterceptorFn } from '@angular/common/http';

export const authInterceptor: HttpInterceptorFn = (req: HttpRequest<any>, next: HttpHandlerFn) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    req = req.clone({
      headers: req.headers.set('Authorization', `Bearer ${token}`)
    });
  }
  return next(req);
};