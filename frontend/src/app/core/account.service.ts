import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom, timeout } from 'rxjs';

export interface Account {
  email: string;
  plan: 'free' | 'pro';
  email_verified: boolean;
  quota: { limit: number; used: number; remaining: number };
}

const REQUEST_TIMEOUT_MS = 8000;
const EXPORT_TIMEOUT_MS = 30000;

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

const int = (value: unknown): number => (typeof value === 'number' && Number.isFinite(value) ? Math.trunc(value) : 0);

/** Valida la cuenta recibida de la red antes de usarla. */
export function parseAccount(raw: unknown): Account | null {
  if (!isRecord(raw) || typeof raw['email'] !== 'string' || !isRecord(raw['quota'])) return null;
  const quota = raw['quota'];
  return {
    email: raw['email'],
    plan: raw['plan'] === 'pro' ? 'pro' : 'free',
    email_verified: raw['email_verified'] === true,
    quota: { limit: int(quota['limit']), used: int(quota['used']), remaining: int(quota['remaining']) },
  };
}

/** Alta, sesión, enlaces del correo y datos de la cuenta (plan y cupo) contra la API. */
@Injectable({ providedIn: 'root' })
export class AccountService {
  private readonly http = inject(HttpClient);

  /**
   * Crea la cuenta. No devuelve sesión: el usuario confirma su email y luego inicia sesión. La respuesta es la misma
   * exista o no el email, así que la pantalla tampoco puede revelarlo.
   */
  async register(email: string, password: string): Promise<void> {
    await this.post('/api/auth/register', { email, password });
  }

  /** Inicia sesión y devuelve el token de sesión. */
  async login(email: string, password: string): Promise<string> {
    const raw = await this.post('/api/auth/login', { email, password });
    const token = isRecord(raw) ? raw['access_token'] : null;
    if (typeof token !== 'string' || !token) throw new Error('Respuesta de la API no válida');
    return token;
  }

  /** Cierra la sesión en el servidor: invalida el token en todos los dispositivos. */
  async logout(): Promise<void> {
    await this.post('/api/auth/logout', {});
  }

  async account(): Promise<Account | null> {
    return parseAccount(await firstValueFrom(this.http.get<unknown>('/api/auth/me').pipe(timeout(REQUEST_TIMEOUT_MS))));
  }

  /** Todo lo que el servicio guarda de la persona (derecho de acceso y portabilidad). */
  exportData(): Promise<unknown> {
    return firstValueFrom(this.http.get<unknown>('/api/auth/export').pipe(timeout(EXPORT_TIMEOUT_MS)));
  }

  /** Borra la cuenta y todos sus datos. Exige la contraseña actual. */
  async deleteAccount(password: string): Promise<void> {
    await this.post('/api/auth/delete-account', { password });
  }

  async verifyEmail(token: string): Promise<void> {
    await this.post('/api/auth/verify-email', { token });
  }

  async resendVerification(): Promise<void> {
    await this.post('/api/auth/resend-verification', {});
  }

  async forgotPassword(email: string): Promise<void> {
    await this.post('/api/auth/forgot-password', { email });
  }

  async resetPassword(token: string, password: string): Promise<void> {
    await this.post('/api/auth/reset-password', { token, password });
  }

  private post(url: string, body: object): Promise<unknown> {
    return firstValueFrom(this.http.post<unknown>(url, body).pipe(timeout(REQUEST_TIMEOUT_MS)));
  }
}
