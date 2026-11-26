import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { esUrlDeLaApi } from '../api.config';
import { AuthService } from '../services/auth';

/** Agrega el token a cada petición a la API y cierra la sesión si el servidor la rechaza. */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  if (!esUrlDeLaApi(req.url)) {
    return next(req);
  }

  const auth = inject(AuthService);
  const token = auth.getToken();
  const peticion = token ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req;

  return next(peticion).pipe(
    catchError((error: HttpErrorResponse) => {
      const esLogin = req.url.includes('/auth/login');
      if (error.status === 401 && token && !esLogin) {
        auth.logout();
      }
      return throwError(() => error);
    })
  );
};
