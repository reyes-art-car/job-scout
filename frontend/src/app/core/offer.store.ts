import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { firstValueFrom, timeout } from 'rxjs';
import { KANBAN_STATUSES, KanbanStatus, NewOffer, Offer } from './models';

export type DataMode = 'loading' | 'api' | 'demo';

interface OfferPage {
  items: Offer[];
}

const STORAGE_KEY = 'jobhunter.demo.offers.v1';
const API_TIMEOUT_MS = 2500;

/**
 * Fuente única de ofertas. Intenta hablar con la API FastAPI (`/api`, vía proxy en desarrollo);
 * si no responde, cae a los datos de demostración y guarda los cambios en el navegador, de modo
 * que la aplicación es totalmente usable desde un hosting estático (p. ej. GitHub Pages).
 */
@Injectable({ providedIn: 'root' })
export class OfferStore {
  private readonly http = inject(HttpClient);

  readonly offers = signal<Offer[]>([]);
  readonly mode = signal<DataMode>('loading');

  readonly stats = computed(() => {
    const all = this.offers();
    const byStatus = Object.fromEntries(KANBAN_STATUSES.map((s) => [s, 0])) as Record<KanbanStatus, number>;
    for (const o of all) byStatus[o.kanban_status] += 1;
    const avg = all.length === 0 ? 0 : Math.round(all.reduce((a, o) => a + o.compatibility, 0) / all.length);
    return {
      total: all.length,
      high: all.filter((o) => o.priority === 'Alta').length,
      avgCompatibility: avg,
      byStatus,
    };
  });

  async load(): Promise<void> {
    try {
      const page = await firstValueFrom(
        this.http.get<OfferPage>('/api/offers', { params: { page_size: 500 } }).pipe(timeout(API_TIMEOUT_MS)),
      );
      // Una API vacía (BD recién creada) no sirve para enseñar la aplicación: se usa la demo.
      if (page.items.length > 0) {
        this.offers.set(page.items);
        this.mode.set('api');
        return;
      }
    } catch {
      // Sin backend: modo demo.
    }
    await this.loadDemo();
  }

  private async loadDemo(): Promise<void> {
    const saved = this.readSaved();
    const offers = saved ?? (await firstValueFrom(this.http.get<Offer[]>('demo/offers.json')));
    this.offers.set(offers);
    this.mode.set('demo');
  }

  async resetDemo(): Promise<void> {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // almacenamiento no disponible
    }
    const offers = await firstValueFrom(this.http.get<Offer[]>('demo/offers.json'));
    this.offers.set(offers);
  }

  async setStatus(offer: Offer, status: KanbanStatus): Promise<void> {
    const apply = (o: Offer) => ({ ...o, kanban_status: status });
    if (this.mode() === 'api') {
      const updated = await firstValueFrom(
        this.http.patch<Offer>(`/api/offers/${offer.id}/status`, { status }),
      );
      this.replace(updated);
      return;
    }
    this.replace(apply(offer));
    this.persist();
  }

  async setNotes(offer: Offer, notes: string): Promise<void> {
    if (this.mode() === 'api') {
      const updated = await firstValueFrom(this.http.patch<Offer>(`/api/offers/${offer.id}`, { notes }));
      this.replace(updated);
      return;
    }
    this.replace({ ...offer, notes });
    this.persist();
  }

  async add(draft: NewOffer): Promise<Offer> {
    if (this.mode() === 'api') {
      const created = await firstValueFrom(this.http.post<Offer>('/api/offers', draft));
      this.offers.update((list) => [created, ...list]);
      return created;
    }
    const list = this.offers();
    const nextNum = list.reduce((max, o) => Math.max(max, Number(o.code.replace(/\D/g, '')) || 0), 0) + 1;
    const created: Offer = {
      ...draft,
      id: list.reduce((max, o) => Math.max(max, o.id), 0) + 1,
      code: `OF${String(nextNum).padStart(3, '0')}`,
      priority: draft.priority ?? (draft.compatibility >= 75 ? 'Alta' : 'Secundaria'),
      adapted_cv_filename: null,
      source: 'document_upload',
    };
    this.offers.set([created, ...list]);
    this.persist();
    return created;
  }

  byId(id: number): Offer | undefined {
    return this.offers().find((o) => o.id === id);
  }

  private replace(updated: Offer): void {
    this.offers.update((list) => list.map((o) => (o.id === updated.id ? updated : o)));
  }

  private readSaved(): Offer[] | null {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? (JSON.parse(raw) as Offer[]) : null;
    } catch {
      return null;
    }
  }

  private persist(): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.offers()));
    } catch {
      // modo privado o cuota agotada: la sesión sigue funcionando sin persistencia
    }
  }
}
