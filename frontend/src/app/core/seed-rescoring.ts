import { CareerData, profileLevels } from './career';
import { Offer, Profile, priorityFor } from './models';
import { analyzeOffer } from './offer-analysis';

/**
 * Las ofertas de ejemplo se puntuaron con otro perfil. Cuando la persona importa su CV se recalculan con sus
 * tecnologías y se limpian el estado y las notas de quien las revisó, para que el panel refleje su caso.
 */
export function rescoreSeed(offers: readonly Offer[], profile: Profile, career: CareerData): Offer[] {
  const levels = profileLevels(profile, career);
  return offers.map((offer) => {
    const analysis = analyzeOffer(offer, '', levels);
    return {
      ...offer,
      compatibility: analysis.coverage,
      priority: priorityFor(analysis.coverage),
      requirements_met: analysis.matched.map((r) => `${r.tech.name} ✓`).join('  '),
      requirements_missing: analysis.missing.map((r) => r.tech.name).join(', ') || 'Ninguno',
      score_reason: 'Estimación automática con las tecnologías de tu CV.',
      kanban_status: 'Pendiente',
      notes: null,
      adapted_cv_filename: null,
    };
  });
}
