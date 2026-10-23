import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { firstValueFrom, timeout } from 'rxjs';

const HTTP_UNAUTHORIZED = 401;
const CHECK_TIMEOUT_MS = 2500;

/**
 * Pide iniciar sesión antes de entrar a la aplicación cuando hay una API que la exige.
 * Sin API (demo estática o `ng serve` sin backend) no hay datos privados que proteger y se deja pasar.
 */
export const accessGuard: CanActivateFn = async () => {
  const http = inject(HttpClient);
  const router = inject(Router);
  try {
    await firstValueFrom(http.get('/api/auth/me').pipe(timeout(CHECK_TIMEOUT_MS)));
    return true;
  } catch (error) {
    return error instanceof HttpErrorResponse && error.status === HTTP_UNAUTHORIZED ? router.createUrlTree(['/acceso']) : true;
  }
};
