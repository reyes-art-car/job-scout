import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { CareerService } from './core/career.service';
import { AuthToken } from './core/auth';
import { OfferStore } from './core/offer.store';
import { ProfileService } from './core/profile.service';
import { IconComponent } from './shared/icon.component';

interface NavItem {
  path: string;
  label: string;
  icon: string;
}

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, IconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  protected readonly store = inject(OfferStore);
  protected readonly career = inject(CareerService);
  private readonly auth = inject(AuthToken);
  protected readonly profile = inject(ProfileService).profile;

  protected readonly nav: NavItem[] = [
    { path: 'panel', label: 'Panel', icon: 'grid' },
    { path: 'ofertas', label: 'Ofertas', icon: 'briefcase' },
    { path: 'adaptar-cv', label: 'Adaptar CV', icon: 'file' },
    { path: 'carta', label: 'Carta de presentación', icon: 'mail' },
    { path: 'skills', label: 'Brecha de skills', icon: 'target' },
    { path: 'mi-perfil', label: 'Mi experiencia', icon: 'check' },
    { path: 'candidaturas', label: 'Mi historial', icon: 'list' },
  ];

  protected async resetDemo(): Promise<void> {
    await this.store.resetDemo();
  }

  protected async connect(event: Event, token: string): Promise<void> {
    event.preventDefault();
    this.auth.set(token);
    await this.store.load();
  }
}
