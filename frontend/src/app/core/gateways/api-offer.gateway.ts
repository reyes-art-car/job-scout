import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, firstValueFrom, timeout } from 'rxjs';
import { KanbanStatus, NewOffer, Offer } from '../models';
import { parseOffers } from '../offer-validation';
import { OfferGateway } from './offer-gateway';

const API_TIMEOUT_MS = 2500;
const PAGE_SIZE = 500;

/** Habla con la API FastAPI (`/api`, con proxy en desarrollo). Valida cada respuesta antes de usarla. */
@Injectable({ providedIn: 'root' })
export class ApiOfferGateway extends OfferGateway {
  private readonly http = inject(HttpClient);

  async list(): Promise<Offer[]> {
    const page = await firstValueFrom(
      this.http
        .get<{ items: unknown }>('/api/offers', { params: { page_size: PAGE_SIZE } })
        .pipe(timeout(API_TIMEOUT_MS)),
    );
    return parseOffers(page.items) ?? [];
  }

  setStatus(offer: Offer, status: KanbanStatus): Promise<Offer> {
    return this.single(this.http.patch<unknown>(`/api/offers/${offer.id}/status`, { status }));
  }

  setNotes(offer: Offer, notes: string): Promise<Offer> {
    return this.single(this.http.patch<unknown>(`/api/offers/${offer.id}`, { notes }));
  }

  add(draft: NewOffer): Promise<Offer> {
    return this.single(this.http.post<unknown>('/api/offers', draft));
  }

  private async single(request: Observable<unknown>): Promise<Offer> {
    const [offer] = parseOffers([await firstValueFrom(request)]) ?? [];
    if (!offer) throw new Error('Respuesta de la API no válida');
    return offer;
  }
}
