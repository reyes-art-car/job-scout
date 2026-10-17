import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { KanbanStatus, NewOffer, Offer, priorityFor } from '../models';
import { CareerService } from '../career.service';
import { parseOffers } from '../offer-validation';
import { ProfileService } from '../profile.service';
import { rescoreSeed } from '../seed-rescoring';
import { OfferGateway } from './offer-gateway';
import { OfferStorage } from './offer-storage';

/** Datos de demostración (`data/demo/offers.json`) con los cambios guardados en el navegador. */
@Injectable({ providedIn: 'root' })
export class DemoOfferGateway extends OfferGateway {
  private readonly http = inject(HttpClient);
  private readonly storage = inject(OfferStorage);
  private readonly profiles = inject(ProfileService);
  private readonly career = inject(CareerService);
  private offers: Offer[] = [];

  async list(): Promise<Offer[]> {
    this.offers = this.storage.read() ?? (await this.loadSeed());
    return this.offers;
  }

  async reset(): Promise<Offer[]> {
    this.storage.clear();
    this.offers = await this.loadSeed();
    return this.offers;
  }

  setStatus(offer: Offer, status: KanbanStatus): Promise<Offer> {
    return this.replace({ ...offer, kanban_status: status });
  }

  setNotes(offer: Offer, notes: string): Promise<Offer> {
    return this.replace({ ...offer, notes });
  }

  add(draft: NewOffer): Promise<Offer> {
    const nextNumber = this.offers.reduce((max, o) => Math.max(max, Number(o.code.replace(/\D/g, '')) || 0), 0) + 1;
    const created: Offer = {
      ...draft,
      id: this.offers.reduce((max, o) => Math.max(max, o.id), 0) + 1,
      code: `OF${String(nextNumber).padStart(3, '0')}`,
      priority: draft.priority ?? priorityFor(draft.compatibility),
      adapted_cv_filename: null,
      source: 'document_upload',
    };
    this.offers = [created, ...this.offers];
    this.storage.write(this.offers);
    return Promise.resolve(created);
  }

  private replace(updated: Offer): Promise<Offer> {
    this.offers = this.offers.map((o) => (o.id === updated.id ? updated : o));
    this.storage.write(this.offers);
    return Promise.resolve(updated);
  }

  private async loadSeed(): Promise<Offer[]> {
    const seed = parseOffers(await firstValueFrom(this.http.get<unknown>('demo/offers.json'))) ?? [];
    // Con un CV importado, las ofertas de ejemplo se puntúan con el perfil de esa persona.
    return this.profiles.isCustom() ? rescoreSeed(seed, this.profiles.profile, this.career.data()) : seed;
  }
}
