import { HttpRequest, HttpHandlerFn, HttpInterceptorFn } from '@angular/common/http';

export const authInterceptor: HttpInterceptorFn = (req: HttpRequest<any>, next: HttpHandlerFn) => {
  const token = localStorage.getItem('access_token');
  console.log('Auth Interceptor - Token:', token);
  if (token) {
    console.log('Auth Interceptor - Adding token');
    req = req.clone({
      headers: req.headers.set('Authorization', `Bearer ${token}`)
    });
  }
  return next(req);
};