import { bootstrapApplication } from '@angular/platform-browser';
import { App } from './app/app';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { authInterceptor } from './app/interceptors/auth-interceptor';
import { provideRouter } from '@angular/router';
import { routes } from './app/app.routes';

bootstrapApplication(App, {
  providers: [
    provideHttpClient(withInterceptors([authInterceptor])),
    provideRouter(routes)
  ]
}).catch(err => console.error(err));