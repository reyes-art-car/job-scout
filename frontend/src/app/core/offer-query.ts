import { KanbanStatus, Offer, Priority } from './models';

export type SortKey = 'compat' | 'fecha' | 'empresa';

export interface OfferQuery {
  text: string;
  status: KanbanStatus | '';
  priority: Priority | '';
  minCompatibility: number;
  sort: SortKey;
}

export const EMPTY_QUERY: OfferQuery = { text: '', status: '', priority: '', minCompatibility: 0, sort: 'compat' };

const COMPARERS: Record<SortKey, (a: Offer, b: Offer) => number> = {
  compat: (a, b) => b.compatibility - a.compatibility,
  fecha: (a, b) => (b.published_date ?? '').localeCompare(a.published_date ?? ''),
  empresa: (a, b) => a.company.localeCompare(b.company),
};

/** Filtra y ordena sin modificar la lista original. */
export function applyQuery(offers: readonly Offer[], query: OfferQuery): Offer[] {
  const text = query.text.trim().toLowerCase();
  return offers
    .filter(
      (o) =>
        (!text || `${o.title} ${o.company} ${o.mandatory_tech}`.toLowerCase().includes(text)) &&
        (!query.status || o.kanban_status === query.status) &&
        (!query.priority || o.priority === query.priority) &&
        o.compatibility >= query.minCompatibility,
    )
    .sort(COMPARERS[query.sort]);
}
