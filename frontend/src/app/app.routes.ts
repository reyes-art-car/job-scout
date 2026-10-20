import { Routes } from '@angular/router';
import { accessGuard } from './core/access.guard';

const SITE = 'Job Hopping & Learning';

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    title: `${SITE} · Cada candidatura te enseña qué aprender`,
    loadComponent: () => import('./features/landing/landing').then((m) => m.Landing),
  },
  {
    path: 'importar-cv',
    title: `Subir mi CV · ${SITE}`,
    loadComponent: () => import('./features/import-cv/import-cv').then((m) => m.ImportCv),
  },
  {
    path: 'acceso',
    title: `Acceso · ${SITE}`,
    loadComponent: () => import('./features/access/access').then((m) => m.Access),
  },
  {
    path: 'verificar',
    title: `Confirmar email · ${SITE}`,
    data: { mode: 'verify' },
    loadComponent: () => import('./features/access/account-action').then((m) => m.AccountAction),
  },
  {
    path: 'recuperar',
    title: `Recuperar contraseña · ${SITE}`,
    data: { mode: 'forgot' },
    loadComponent: () => import('./features/access/account-action').then((m) => m.AccountAction),
  },
  {
    path: 'restablecer',
    title: `Nueva contraseña · ${SITE}`,
    data: { mode: 'reset' },
    loadComponent: () => import('./features/access/account-action').then((m) => m.AccountAction),
  },
  {
    path: 'aviso-legal',
    title: `Aviso legal · ${SITE}`,
    loadComponent: () => import('./features/legal/aviso-legal').then((m) => m.AvisoLegal),
  },
  {
    path: 'privacidad',
    title: `Política de privacidad · ${SITE}`,
    loadComponent: () => import('./features/legal/privacidad').then((m) => m.Privacidad),
  },
  {
    path: 'cookies',
    title: `Política de cookies · ${SITE}`,
    loadComponent: () => import('./features/legal/cookies').then((m) => m.Cookies),
  },
  {
    path: 'condiciones',
    title: `Condiciones de uso · ${SITE}`,
    loadComponent: () => import('./features/legal/condiciones').then((m) => m.Condiciones),
  },
  {
    path: '',
    canActivate: [accessGuard],
    loadComponent: () => import('./shell/app-shell').then((m) => m.AppShell),
    children: [
      {
        path: 'buscar',
        title: `Buscar ofertas · ${SITE}`,
        loadComponent: () => import('./features/search/search').then((m) => m.Search),
      },
      {
        path: 'panel',
        title: `Panel · ${SITE}`,
        loadComponent: () => import('./features/dashboard/dashboard').then((m) => m.Dashboard),
      },
      {
        path: 'ofertas',
        title: `Ofertas · ${SITE}`,
        loadComponent: () => import('./features/offers/offers').then((m) => m.Offers),
      },
      {
        path: 'adaptar-cv',
        title: `Adaptar CV · ${SITE}`,
        loadComponent: () => import('./features/cv/cv-adapter').then((m) => m.CvAdapter),
      },
      {
        path: 'carta',
        title: `Carta de presentación · ${SITE}`,
        loadComponent: () => import('./features/cover-letter/cover-letter').then((m) => m.CoverLetter),
      },
      {
        path: 'skills',
        title: `Brecha de skills · ${SITE}`,
        loadComponent: () => import('./features/skills/skills-gap').then((m) => m.SkillsGap),
      },
      {
        path: 'mi-perfil',
        title: `Mi experiencia · ${SITE}`,
        loadComponent: () => import('./features/career/profile').then((m) => m.CareerProfile),
      },
      {
        path: 'candidaturas',
        title: `Mi historial · ${SITE}`,
        loadComponent: () => import('./features/career/history').then((m) => m.ApplicationHistory),
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
