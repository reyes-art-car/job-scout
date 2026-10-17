import { Injectable } from '@angular/core';

/** Claves de `localStorage` que escribe la aplicación. Es todo lo que se guarda de una persona. */
export const LOCAL_DATA_KEYS = ['jobhunter.profile.v1', 'jobhunter.demo.offers.v1', 'jobscout.career.v1'] as const;

@Injectable({ providedIn: 'root' })
export class LocalDataService {
  /** Derecho de supresión: borra el CV importado, las ofertas y el progreso guardados en este navegador. */
  clearAll(): void {
    for (const key of LOCAL_DATA_KEYS) {
      try {
        localStorage.removeItem(key);
      } catch {
        // almacenamiento no disponible: no hay nada guardado que borrar
      }
    }
  }
}
