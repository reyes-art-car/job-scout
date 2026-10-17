import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { Profile } from './models';

@Injectable({ providedIn: 'root' })
export class ProfileService {
  private readonly http = inject(HttpClient);
  private readonly loaded = signal<Profile | null>(null);

  async load(): Promise<void> {
    this.loaded.set(await firstValueFrom(this.http.get<Profile>('demo/profile.json')));
  }

  /** Solo se llama tras el inicializador de la app, que garantiza que el perfil está cargado. */
  get profile(): Profile {
    const value = this.loaded();
    if (value === null) throw new Error('El perfil aún no se ha cargado');
    return value;
  }
}
