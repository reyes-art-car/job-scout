import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { AccountService } from '../../core/account.service';

const HTTP_BAD_REQUEST = 400;
const HTTP_VALIDATION = 422;
const HTTP_TOO_MANY = 429;
const MIN_PASSWORD_LENGTH = 10;

export type ActionMode = 'verify' | 'forgot' | 'reset';

/**
 * Pantallas de los enlaces del correo: confirmar el email, pedir un enlace para recuperar la contraseña y elegir una
 * contraseña nueva. El token llega en la URL; se retira de la barra de direcciones en cuanto se lee.
 */
@Component({
  selector: 'app-account-action',
  imports: [RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './account-action.html',
  styleUrl: './access.scss',
})
export class AccountAction implements OnInit {
  private readonly api = inject(AccountService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  protected readonly mode: ActionMode = this.route.snapshot.data['mode'] as ActionMode;
  protected readonly busy = signal(false);
  protected readonly error = signal('');
  protected readonly done = signal('');
  protected readonly minPassword = MIN_PASSWORD_LENGTH;
  private token = '';

  async ngOnInit(): Promise<void> {
    this.token = this.route.snapshot.queryParamMap.get('token') ?? '';
    if (this.token) {
      // Que el token no se quede en el historial del navegador ni se copie al compartir la dirección.
      await this.router.navigate([], { queryParams: { token: null }, queryParamsHandling: 'merge', replaceUrl: true });
    }
    if (this.mode === 'verify') await this.verify();
  }

  protected async forgot(event: Event, email: string): Promise<void> {
    event.preventDefault();
    await this.run(async () => {
      await this.api.forgotPassword(email);
      this.done.set('Si el email tiene cuenta, te hemos enviado un enlace para elegir una contraseña nueva.');
    });
  }

  protected async reset(event: Event): Promise<void> {
    event.preventDefault();
    const password = String(new FormData(event.target as HTMLFormElement).get('password') ?? '');
    await this.run(async () => {
      await this.api.resetPassword(this.token, password);
      this.token = '';
      this.done.set('Contraseña cambiada. Se han cerrado todas tus sesiones: inicia sesión con la nueva.');
    });
  }

  protected get hasToken(): boolean {
    return this.token !== '';
  }

  private async verify(): Promise<void> {
    if (!this.token) {
      this.error.set('Falta el enlace de confirmación. Abre el enlace que te enviamos por correo.');
      return;
    }
    await this.run(async () => {
      await this.api.verifyEmail(this.token);
      this.done.set('Email confirmado. Ya puedes iniciar sesión y lanzar búsquedas.');
    });
  }

  private async run(action: () => Promise<void>): Promise<void> {
    this.busy.set(true);
    this.error.set('');
    try {
      await action();
    } catch (error) {
      this.error.set(this.message(error));
    } finally {
      this.busy.set(false);
    }
  }

  private message(error: unknown): string {
    if (!(error instanceof HttpErrorResponse)) return 'No se pudo conectar. Inténtalo de nuevo en un momento.';
    if (error.status === HTTP_BAD_REQUEST) return 'El enlace no es válido o ha caducado. Pide uno nuevo.';
    if (error.status === HTTP_VALIDATION) return `Revisa los datos: la contraseña necesita al menos ${MIN_PASSWORD_LENGTH} caracteres.`;
    if (error.status === HTTP_TOO_MANY) return 'Demasiados intentos. Espera unos minutos.';
    return 'No se pudo completar la acción. Inténtalo de nuevo en un momento.';
  }
}
