import { Routes } from '@angular/router';

const SITE = 'Job Hopper & Learning';

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    title: `${SITE} · Tu búsqueda de empleo IT, a partir de tu CV`,
    loadComponent: () => import('./features/landing/landing').then((m) => m.Landing),
  },
  {
    path: 'importar-cv',
    title: `Subir mi CV · ${SITE}`,
    loadComponent: () => import('./features/import-cv/import-cv').then((m) => m.ImportCv),
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
    loadComponent: () => import('./shell/app-shell').then((m) => m.AppShell),
    children: [
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
