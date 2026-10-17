import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { IconComponent } from './icon.component';

/** Marco de las páginas públicas (landing, importación y textos legales). No interviene en los datos. */
@Component({
  selector: 'app-public-shell',
  imports: [RouterLink, IconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <a class="skip-link" href="#public-content">Ir al contenido</a>
    <header class="top">
      <a class="brand" routerLink="/" aria-label="Job Hopping &amp; Learning, inicio">
        <span class="logo"><app-icon name="target" [size]="18" /></span>
        <span><strong>Job Hopping</strong><small>&amp; Learning</small></span>
      </a>
      <nav aria-label="Principal">
        <a routerLink="/" fragment="como-funciona">Cómo funciona</a>
        <a routerLink="/panel">Ver la demo</a>
        <a class="cta" routerLink="/importar-cv">Subir mi CV</a>
      </nav>
    </header>
    <main id="public-content" tabindex="-1"><ng-content /></main>
    <footer class="foot">
      <p>
        Job Hopping &amp; Learning es un proyecto personal de portfolio de María Reyes Artacho Carrero. Gratuito y sin cuentas:
        tu CV se queda en tu navegador.
      </p>
      <nav aria-label="Información legal">
        <a routerLink="/aviso-legal">Aviso legal</a>
        <a routerLink="/privacidad">Privacidad</a>
        <a routerLink="/cookies">Cookies</a>
        <a routerLink="/condiciones">Condiciones de uso</a>
        <a href="https://github.com/reyes-art-car/job-scout" target="_blank" rel="noopener noreferrer">Código en GitHub</a>
      </nav>
    </footer>
  `,
  styleUrl: './public-shell.scss',
})
export class PublicShell {}
