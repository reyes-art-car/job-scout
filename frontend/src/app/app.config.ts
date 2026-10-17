import {
  ApplicationConfig,
  inject,
  provideAppInitializer,
  provideBrowserGlobalErrorListeners,
  provideZoneChangeDetection,
} from '@angular/core';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter, withHashLocation } from '@angular/router';

import { routes } from './app.routes';
import { OfferStore } from './core/offer.store';
import { ProfileService } from './core/profile.service';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideZoneChangeDetection({ eventCoalescing: true }),
    // Hash routing: funciona igual en `ng serve`, en el backend y en hostings estáticos (GitHub Pages).
    provideRouter(routes, withHashLocation()),
    provideHttpClient(),
    provideAppInitializer(() => {
      const profile = inject(ProfileService);
      const store = inject(OfferStore);
      return Promise.all([profile.load(), store.load()]);
    }),
  ],
};
