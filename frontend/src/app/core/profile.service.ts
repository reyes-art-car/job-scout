import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { Profile } from './models';
import { parseProfile } from './profile-validation';

export const PROFILE_STORAGE_KEY = 'jobhunter.profile.v1';

/**
 * Perfil con el que trabaja toda la aplicación: el de la demo o el que la persona ha importado desde su CV.
 * Lo importado se queda en este navegador (`localStorage`); no se envía a ningún servidor.
 */
@Injectable({ providedIn: 'root' })
export class ProfileService {
  private readonly http = inject(HttpClient);
  private readonly loaded = signal<Profile | null>(null);
  /** `true` cuando el perfil procede de un CV importado y no de la demo. */
  readonly isCustom = signal(false);

  async load(): Promise<void> {
    const stored = this.readStored();
    if (stored) {
      this.loaded.set(stored);
      this.isCustom.set(true);
      return;
    }
    this.loaded.set(await firstValueFrom(this.http.get<Profile>('demo/profile.json')));
    this.isCustom.set(false);
  }

  /** Solo se llama tras el inicializador de la app, que garantiza que el perfil está cargado. */
  get profile(): Profile {
    const value = this.loaded();
    if (value === null) throw new Error('El perfil aún no se ha cargado');
    return value;
  }

  /** Guarda el perfil importado. Devuelve `false` si no es válido o el navegador no deja guardarlo. */
  saveCustom(candidate: unknown): boolean {
    const profile = parseProfile(candidate);
    if (profile === null) return false;
    try {
      localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(profile));
    } catch {
      return false;
    }
    this.loaded.set(profile);
    this.isCustom.set(true);
    return true;
  }

  private readStored(): Profile | null {
    try {
      const raw = localStorage.getItem(PROFILE_STORAGE_KEY);
      return raw ? parseProfile(JSON.parse(raw)) : null;
    } catch {
      return null;
    }
  }
}
