import { Offer } from './models';
import { analyzeOffer } from './offer-analysis';
import { Tech } from './tech-catalog';

export interface TechDemand {
  tech: Tech;
  /** Nº de ofertas que mencionan la tecnología (en cualquier apartado). */
  offers: number;
  /** Nº de ofertas donde figura como obligatoria. */
  mandatory: number;
  /** Porcentaje sobre el total de ofertas analizadas. */
  share: number;
}

/** Frecuencia de cada tecnología del catálogo en el conjunto de ofertas. */
export function techDemand(offers: readonly Offer[]): TechDemand[] {
  const counts = new Map<string, { tech: Tech; offers: number; mandatory: number }>();
  for (const offer of offers) {
    for (const req of analyzeOffer(offer).requirements) {
      const entry = counts.get(req.tech.id) ?? { tech: req.tech, offers: 0, mandatory: 0 };
      entry.offers += 1;
      if (req.origin === 'obligatoria') entry.mandatory += 1;
      counts.set(req.tech.id, entry);
    }
  }
  const total = Math.max(offers.length, 1);
  return [...counts.values()]
    .map((c) => ({ ...c, share: Math.round((c.offers / total) * 100) }))
    .sort((a, b) => b.mandatory * 2 + b.offers - (a.mandatory * 2 + a.offers));
}
