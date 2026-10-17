import { Injectable, inject } from '@angular/core';
import { Offer } from '../models';
import { parseOffers } from '../offer-validation';

/** Persistencia local de la demo, detrás de una abstracción para poder sustituirla en las pruebas. */
@Injectable({ providedIn: 'root', useFactory: () => inject(LocalOfferStorage) })
export abstract class OfferStorage {
  abstract read(): Offer[] | null;
  abstract write(offers: readonly Offer[]): void;
  abstract clear(): void;
}

const STORAGE_KEY = 'jobhunter.demo.offers.v1';

@Injectable({ providedIn: 'root' })
export class LocalOfferStorage extends OfferStorage {
  /** Lo guardado se valida igual que una respuesta de red: nadie debe poder romper la app editando localStorage. */
  read(): Offer[] | null {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? parseOffers(JSON.parse(raw)) : null;
    } catch {
      return null;
    }
  }

  write(offers: readonly Offer[]): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(offers));
    } catch {
      // modo privado o cuota agotada: la sesión sigue funcionando sin persistencia
    }
  }

  clear(): void {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // almacenamiento no disponible
    }
  }
}
