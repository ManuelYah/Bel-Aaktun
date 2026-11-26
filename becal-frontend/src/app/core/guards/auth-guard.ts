import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth';

/** Cualquier persona con sesión iniciada. */
export const authGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  return authService.isLoggedIn() ? true : router.createUrlTree(['/login']);
};

/** Panel del artesano. Un administrador va a su propio panel. */
export const artesanoGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (!authService.isLoggedIn()) {
    return router.createUrlTree(['/login']);
  }
  return authService.isAdmin() ? router.createUrlTree(['/admin']) : true;
};

/** Panel de administración: solo el rol ADMIN. */
export const adminGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isAdmin()) {
    return true;
  }
  return router.createUrlTree([authService.isLoggedIn() ? '/dashboard' : '/login']);
};
