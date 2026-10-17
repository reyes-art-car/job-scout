import { Offer } from './models';
import { LEVEL_WEIGHT, Tech, TechLevel, detectTechs } from './tech-catalog';

export type Role = 'backend' | 'fullstack' | 'frontend';
export type Origin = 'obligatoria' | 'deseable' | 'texto';

export interface Requirement {
  tech: Tech;
  weight: number;
  origin: Origin;
}

export interface OfferAnalysis {
  requirements: Requirement[];
  matched: Requirement[];
  partial: Requirement[];
  missing: Requirement[];
  /** 0-100: peso de requisitos cubiertos (parcial cuenta 0,5) sobre el peso total. */
  coverage: number;
  role: Role;
}

export type OfferInput = Pick<Offer, 'title' | 'mandatory_tech' | 'desirable_tech'> & Partial<Pick<Offer, 'modality'>>;

const WEIGHT: Record<Origin, number> = { obligatoria: 3, texto: 1.5, deseable: 1 };
const ENGLISH_WEIGHT = 0.5; // «inglés» no distingue candidatos: se muestra, pero casi no pesa
const BACKEND_MAX_FRONT_RATIO = 0.2;
const FRONTEND_MIN_FRONT_RATIO = 0.65;
const GENERIC_STACK = ['Java', 'Spring Boot', 'Angular'];
const NOT_DISTINCTIVE = ['english', 'excel-csv', 'git'];

export function extractRequirements(offer: OfferInput, description = ''): Requirement[] {
  const found = new Map<string, Requirement>();
  const add = (techs: Tech[], origin: Origin) => {
    for (const tech of techs) {
      const previous = found.get(tech.id);
      if (!previous || WEIGHT[origin] > previous.weight) {
        found.set(tech.id, { tech, weight: WEIGHT[origin], origin });
      }
    }
  };
  // De menor a mayor peso: si una tecnología aparece en varios apartados, gana el más exigente.
  add(detectTechs(offer.desirable_tech), 'deseable');
  add(detectTechs(description), 'texto');
  add(detectTechs(offer.title), 'texto');
  add(detectTechs(offer.mandatory_tech), 'obligatoria');
  const english = found.get('english');
  if (english) found.set('english', { ...english, weight: ENGLISH_WEIGHT });
  return [...found.values()].sort((a, b) => b.weight - a.weight);
}

function detectRole(offer: OfferInput, requirements: Requirement[]): Role {
  const title = offer.title.toLowerCase();
  if (/full\s*-?\s*stack/.test(title)) return 'fullstack';
  if (/back\s*-?\s*end/.test(title)) return 'backend';
  if (/front\s*-?\s*end/.test(title)) return 'frontend';
  let front = 0;
  let back = 0;
  for (const r of requirements) {
    if (r.tech.id === 'android') continue;
    if (r.tech.category === 'Frontend') front += r.weight;
    else if (r.tech.category === 'Backend') back += r.weight;
  }
  if (front + back === 0) return 'fullstack';
  const frontRatio = front / (front + back);
  if (frontRatio < BACKEND_MAX_FRONT_RATIO) return 'backend';
  if (frontRatio > FRONTEND_MIN_FRONT_RATIO) return 'frontend';
  return 'fullstack';
}

const sumWeights = (items: Requirement[], factor: (r: Requirement) => number): number =>
  items.reduce((sum, r) => sum + r.weight * factor(r), 0);

export function analyzeOffer(offer: OfferInput, description = '', levels: Record<string, TechLevel> = {}, corrected?: Requirement[]): OfferAnalysis {
  const requirements = corrected ?? extractRequirements(offer, description).map(r => ({ ...r, tech: { ...r.tech, level: levels[r.tech.id] ?? r.tech.level } }));
  const total = sumWeights(requirements, () => 1);
  const covered = sumWeights(requirements, (r) => LEVEL_WEIGHT[r.tech.level]);
  return {
    requirements,
    matched: requirements.filter((r) => r.tech.level === 'have'),
    partial: requirements.filter((r) => r.tech.level === 'partial'),
    missing: requirements.filter((r) => r.tech.level === 'gap'),
    coverage: total === 0 ? 0 : Math.round((covered / total) * 100),
    role: detectRole(offer, requirements),
  };
}

/** Tecnologías acreditadas más relevantes para la oferta (para titulares y resúmenes). */
export function topMatched(analysis: OfferAnalysis, count = 3): string[] {
  const names = analysis.matched
    .filter((r) => !NOT_DISTINCTIVE.includes(r.tech.id))
    .slice(0, count)
    .map((r) => r.tech.name);
  return names.length > 0 ? names : GENERIC_STACK.slice(0, count);
}
