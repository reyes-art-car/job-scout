import { HttpInterceptorFn } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';

const TOKEN_KEY = 'jobhunter.api.token';

/**
 * Token de acceso a la API. Se guarda en `sessionStorage` (se borra al cerrar la pestaña), nunca en
 * `localStorage`, y solo se envía a rutas `/api/`: jamás a un dominio de terceros.
 */
@Injectable({ providedIn: 'root' })
export class AuthToken {
  private readonly current = signal<string | null>(this.read());
  readonly token = this.current.asReadonly();

  set(token: string): void {
    const clean = token.trim();
    this.current.set(clean || null);
    try {
      if (clean) sessionStorage.setItem(TOKEN_KEY, clean);
      else sessionStorage.removeItem(TOKEN_KEY);
    } catch {
      // sin almacenamiento: el token vive solo en memoria
    }
  }

  private read(): string | null {
    try {
      return sessionStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  }
}

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = inject(AuthToken).token();
  const isApi = req.url.startsWith('/api/');
  return token && isApi ? next(req.clone({ setHeaders: { Authorization: `Bearer ${token}` } })) : next(req);
};
