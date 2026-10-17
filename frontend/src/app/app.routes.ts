import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'panel' },
  {
    path: 'panel',
    title: 'Panel · JobHunter',
    loadComponent: () => import('./features/dashboard/dashboard').then((m) => m.Dashboard),
  },
  {
    path: 'ofertas',
    title: 'Ofertas · JobHunter',
    loadComponent: () => import('./features/offers/offers').then((m) => m.Offers),
  },
  {
    path: 'adaptar-cv',
    title: 'Adaptar CV · JobHunter',
    loadComponent: () => import('./features/cv/cv-adapter').then((m) => m.CvAdapter),
  },
  {
    path: 'carta',
    title: 'Carta de presentación · JobHunter',
    loadComponent: () => import('./features/cover-letter/cover-letter').then((m) => m.CoverLetter),
  },
  {
    path: 'skills',
    title: 'Brecha de skills · JobHunter',
    loadComponent: () => import('./features/skills/skills-gap').then((m) => m.SkillsGap),
  },
  { path: '**', redirectTo: 'panel' },
];
