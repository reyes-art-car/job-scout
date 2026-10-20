import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { AccountService } from '../../core/account.service';
import { AuthToken } from '../../core/auth';
import { OfferStore } from '../../core/offer.store';

const HTTP_UNAUTHORIZED = 401;
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
  private readonly api = inject(AccountService);
  private readonly auth = inject(AuthToken);
  private readonly store = inject(OfferStore);
  private readonly router = inject(Router);

  protected readonly mode = signal<Mode>('login');
  protected readonly busy = signal(false);
  protected readonly error = signal('');
  /** Tras el alta: aviso de que se ha enviado un correo (igual exista o no la cuenta). */
  protected readonly notice = signal('');
  protected readonly minPassword = MIN_PASSWORD_LENGTH;

  protected switchTo(mode: Mode): void {
    this.mode.set(mode);
    this.error.set('');
    this.notice.set('');
  }

  protected async submit(event: Event, email: string, password: string): Promise<void> {
    event.preventDefault();
    this.busy.set(true);
    this.error.set('');
    this.notice.set('');
    try {
      if (this.mode() === 'register') {
        await this.api.register(email, password);
        this.mode.set('login');
        this.notice.set('Te hemos enviado un correo para confirmar tu cuenta. Ábrelo y después inicia sesión.');
        return;
      }
      this.auth.set(await this.api.login(email, password));
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
      case HTTP_FORBIDDEN:
        return 'El registro de cuentas nuevas está cerrado por ahora.';
      case HTTP_VALIDATION:
        return `Revisa el email y usa una contraseña de al menos ${MIN_PASSWORD_LENGTH} caracteres.`;
      case HTTP_TOO_MANY:
        return 'Demasiados intentos. Espera unos minutos antes de volver a probar.';
      default:
        return 'No se pudo conectar. Inténtalo de nuevo en un momento.';
    }
  }
}
