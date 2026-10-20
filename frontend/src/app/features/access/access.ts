import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { AuthToken } from '../../core/auth';
import { OfferStore } from '../../core/offer.store';
import { SearchService } from '../../core/search.service';

const HTTP_UNAUTHORIZED = 401;
const HTTP_CONFLICT = 409;
const HTTP_FORBIDDEN = 403;
const HTTP_VALIDATION = 422;
const HTTP_TOO_MANY = 429;
const MIN_PASSWORD_LENGTH = 10;

type Mode = 'login' | 'register';

/** Entrada a la aplicación: inicio de sesión o alta de cuenta con email y contraseña. */
@Component({
  selector: 'app-access',
  imports: [RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './access.html',
  styleUrl: './access.scss',
})
export class Access {
  private readonly api = inject(SearchService);
  private readonly auth = inject(AuthToken);
  private readonly store = inject(OfferStore);
  private readonly router = inject(Router);

  protected readonly mode = signal<Mode>('login');
  protected readonly busy = signal(false);
  protected readonly error = signal('');
  protected readonly minPassword = MIN_PASSWORD_LENGTH;

  protected switchTo(mode: Mode): void {
    this.mode.set(mode);
    this.error.set('');
  }

  protected async submit(event: Event, email: string, password: string): Promise<void> {
    event.preventDefault();
    this.busy.set(true);
    this.error.set('');
    try {
      const token =
        this.mode() === 'register' ? await this.api.register(email, password) : await this.api.login(email, password);
      this.auth.set(token);
      await this.store.load();
      await this.router.navigateByUrl('/buscar');
    } catch (error) {
      this.auth.set('');
      this.error.set(this.message(error));
    } finally {
      this.busy.set(false);
    }
  }

  private message(error: unknown): string {
    if (!(error instanceof HttpErrorResponse)) return 'No se pudo conectar. Inténtalo de nuevo en un momento.';
    switch (error.status) {
      case HTTP_UNAUTHORIZED:
        return 'Email o contraseña incorrectos.';
      case HTTP_CONFLICT:
        return 'Ya existe una cuenta con ese email.';
      case HTTP_FORBIDDEN:
        return 'El registro de cuentas nuevas está cerrado por ahora.';
      case HTTP_VALIDATION:
        return `Revisa el email y usa una contraseña de al menos ${MIN_PASSWORD_LENGTH} caracteres.`;
      case HTTP_TOO_MANY:
        return 'Demasiados intentos. Espera un minuto.';
      default:
        return 'No se pudo conectar. Inténtalo de nuevo en un momento.';
    }
  }
}
