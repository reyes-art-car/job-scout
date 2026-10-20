import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AuthToken } from '../core/auth';
import { CareerService } from '../core/career.service';
import { LocalDataService } from '../core/local-data.service';
import { OfferStore } from '../core/offer.store';
import { ProfileService } from '../core/profile.service';
import { IconComponent } from '../shared/icon.component';

interface NavItem {
  path: string;
  label: string;
  icon: string;
}

/** Marco de la aplicación: menú lateral con el estado de los datos y el área de trabajo. */
@Component({
  selector: 'app-shell',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, IconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './app-shell.html',
  styleUrl: './app-shell.scss',
})
export class AppShell {
  protected readonly store = inject(OfferStore);
  protected readonly career = inject(CareerService);
  protected readonly profileService = inject(ProfileService);
  private readonly auth = inject(AuthToken);
  private readonly router = inject(Router);
  private readonly localData = inject(LocalDataService);

  protected readonly nav: NavItem[] = [
    { path: '/buscar', label: 'Buscar ofertas', icon: 'target' },
    { path: '/panel', label: 'Panel', icon: 'grid' },
    { path: '/ofertas', label: 'Ofertas', icon: 'briefcase' },
    { path: '/adaptar-cv', label: 'Adaptar CV', icon: 'file' },
    { path: '/carta', label: 'Carta de presentación', icon: 'mail' },
    { path: '/skills', label: 'Brecha de skills', icon: 'target' },
    { path: '/mi-perfil', label: 'Mi experiencia', icon: 'check' },
    { path: '/candidaturas', label: 'Mi historial', icon: 'list' },
  ];

  protected async resetDemo(): Promise<void> {
    await this.store.resetDemo();
  }

  /** Derecho de supresión: borra todo lo guardado en este navegador y vuelve al inicio. */
  protected eraseMyData(): void {
    if (!window.confirm('Se borrarán tu CV, tus ofertas y tu progreso guardados en este navegador. ¿Continuar?')) return;
    this.localData.clearAll();
    window.location.hash = '#/';
    window.location.reload();
  }

  protected readonly loggedIn = this.auth.token;

  protected async logout(): Promise<void> {
    this.auth.set('');
    await this.router.navigateByUrl('/acceso');
  }
}
