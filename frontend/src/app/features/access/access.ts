import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { firstValueFrom, timeout } from 'rxjs';
import { AuthToken } from '../../core/auth';
import { OfferStore } from '../../core/offer.store';

const HTTP_UNAUTHORIZED = 401;
const CHECK_TIMEOUT_MS = 4000;

/** Pantalla de clave de acceso: la API solo responde a quien la conoce. */
@Component({
  selector: 'app-access',
  imports: [RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './access.html',
  styleUrl: './access.scss',
})
export class Access {
  private readonly http = inject(HttpClient);
  private readonly auth = inject(AuthToken);
  private readonly store = inject(OfferStore);
  private readonly router = inject(Router);

  protected readonly busy = signal(false);
  protected readonly error = signal('');

  protected async submit(event: Event, key: string): Promise<void> {
    event.preventDefault();
    this.busy.set(true);
    this.error.set('');
    this.auth.set(key);
    try {
      await firstValueFrom(this.http.get('/api/auth/check', { responseType: 'text' }).pipe(timeout(CHECK_TIMEOUT_MS)));
      await this.store.load();
      await this.router.navigateByUrl('/panel');
    } catch (error) {
      this.auth.set('');
      this.error.set(
        error instanceof HttpErrorResponse && error.status === HTTP_UNAUTHORIZED
          ? 'Clave incorrecta.'
          : 'No se pudo comprobar la clave. Inténtalo de nuevo en un momento.',
      );
    } finally {
      this.busy.set(false);
    }
  }
}
