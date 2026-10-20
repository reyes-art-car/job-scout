import { HttpErrorResponse } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { AuthToken } from './auth';
import { CareerService } from './career.service';
import { ApiOfferGateway } from './gateways/api-offer.gateway';
import { DemoOfferGateway } from './gateways/demo-offer.gateway';
import { OfferGateway } from './gateways/offer-gateway';
import { KANBAN_STATUSES, KanbanStatus, NewOffer, Offer } from './models';

export type DataMode = 'loading' | 'api' | 'demo';

const HTTP_UNAUTHORIZED = 401;

/**
 * Estado de las ofertas para toda la aplicación. Delega el acceso a datos en un `OfferGateway`:
 * la API si responde y tiene datos y, si no, la demo con persistencia en el navegador. Por eso la misma
 * aplicación funciona en local con backend y en un hosting estático (GitHub Pages).
 */
@Injectable({ providedIn: 'root' })
export class OfferStore {
  private readonly api = inject(ApiOfferGateway);
  private readonly auth = inject(AuthToken);
  private readonly career = inject(CareerService);
  private readonly demo = inject(DemoOfferGateway);
  private gateway: OfferGateway = this.demo;

  readonly offers = signal<Offer[]>([]);
  readonly mode = signal<DataMode>('loading');
  /** La API respondió 401: hace falta iniciar sesión. */
  readonly authRequired = signal(false);

  readonly stats = computed(() => {
    const all = this.offers();
    const byStatus = Object.fromEntries(KANBAN_STATUSES.map((s) => [s, 0])) as Record<KanbanStatus, number>;
    for (const o of all) byStatus[o.kanban_status] += 1;
    const avg = all.length === 0 ? 0 : Math.round(all.reduce((sum, o) => sum + o.compatibility, 0) / all.length);
    return {
      total: all.length,
      high: all.filter((o) => o.priority === 'Alta').length,
      avgCompatibility: avg,
      byStatus,
    };
  });

  async load(): Promise<void> {
    this.authRequired.set(false);
    try {
      const items = await this.api.list();
      // Una API vacía sin sesión (BD recién creada) no sirve para enseñar la aplicación: se usa la demo.
      // Con sesión iniciada, en cambio, «vacío» es la verdad: una cuenta nueva aún no tiene ofertas.
      if (items.length > 0 || this.auth.token() !== null) {
        this.use(this.api, items, 'api');
        return;
      }
    } catch (error) {
      if (error instanceof HttpErrorResponse && error.status === HTTP_UNAUTHORIZED) this.authRequired.set(true);
    }
    this.use(this.demo, await this.demo.list(), 'demo');
  }

  async resetDemo(): Promise<void> {
    this.offers.set(await this.demo.reset());
  }

  async setStatus(offer: Offer, status: KanbanStatus): Promise<void> {
    const updated = await this.gateway.setStatus(offer, status);
    this.career.recordStatus(offer, this.mode(), status);
    this.replace(updated);
  }

  async setNotes(offer: Offer, notes: string): Promise<void> {
    this.replace(await this.gateway.setNotes(offer, notes));
  }

  async add(draft: NewOffer): Promise<Offer> {
    const created = await this.gateway.add(draft);
    this.offers.update((list) => [created, ...list]);
    return created;
  }

  byId(id: number): Offer | undefined {
    return this.offers().find((o) => o.id === id);
  }

  private use(gateway: OfferGateway, offers: Offer[], mode: DataMode): void {
    this.gateway = gateway;
    this.offers.set(offers);
    this.mode.set(mode);
  }

  private replace(updated: Offer): void {
    this.offers.update((list) => list.map((o) => (o.id === updated.id ? updated : o)));
  }
}
