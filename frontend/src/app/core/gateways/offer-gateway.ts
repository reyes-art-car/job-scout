import { KanbanStatus, NewOffer, Offer } from '../models';

/**
 * Puerto de acceso a las ofertas. `OfferStore` solo conoce esta clase abstracta: no sabe si los datos
 * vienen de la API o de la demo (inversión de dependencias) y se puede añadir otro origen sin tocarla.
 */
export abstract class OfferGateway {
  abstract list(): Promise<Offer[]>;
  abstract setStatus(offer: Offer, status: KanbanStatus): Promise<Offer>;
  abstract setNotes(offer: Offer, notes: string): Promise<Offer>;
  abstract add(draft: NewOffer): Promise<Offer>;
}
