import { LEVEL_WEIGHT, Tech, detectTechs } from './tech-catalog';
import { Offer, Profile, SkillGroup, SkillsOrder } from './models';

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

export interface SkillItem {
  text: string;
  hit: boolean;
}

export interface TailoredGroup {
  label: string;
  items: SkillItem[];
}

export interface TailoredBullet {
  text: string;
  score: number;
  originalIndex: number;
}

export interface TailoredCv {
  analysis: OfferAnalysis;
  title: string;
  summary: string;
  bullets: TailoredBullet[];
  skillsOrder: SkillsOrder;
  groups: TailoredGroup[];
}

export type OfferInput = Pick<Offer, 'title' | 'mandatory_tech' | 'desirable_tech'> &
  Partial<Pick<Offer, 'modality'>>;

const WEIGHT: Record<Origin, number> = { obligatoria: 3, texto: 1.5, deseable: 1 };
const ROLE_LABEL: Record<Role, string> = {
  backend: 'JAVA BACKEND DEVELOPER',
  fullstack: 'FULL STACK DEVELOPER',
  frontend: 'FRONTEND DEVELOPER',
};

export function extractRequirements(offer: OfferInput, description = ''): Requirement[] {
  const found = new Map<string, Requirement>();
  const add = (techs: Tech[], origin: Origin) => {
    for (const tech of techs) {
      const prev = found.get(tech.id);
      if (!prev || WEIGHT[origin] > prev.weight) {
        found.set(tech.id, { tech, weight: WEIGHT[origin], origin });
      }
    }
  };
  add(detectTechs(offer.desirable_tech), 'deseable');
  add(detectTechs(description), 'texto');
  add(detectTechs(offer.title), 'texto');
  add(detectTechs(offer.mandatory_tech), 'obligatoria');
  // «English» no distingue candidatos: se muestra, pero con peso mínimo.
  const english = found.get('english');
  if (english) found.set('english', { ...english, weight: 0.5 });
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
  const ratio = front / (front + back);
  if (ratio < 0.2) return 'backend';
  if (ratio > 0.65) return 'frontend';
  return 'fullstack';
}

export function analyzeOffer(offer: OfferInput, description = ''): OfferAnalysis {
  const requirements = extractRequirements(offer, description);
  const matched = requirements.filter((r) => r.tech.level === 'have');
  const partial = requirements.filter((r) => r.tech.level === 'partial');
  const missing = requirements.filter((r) => r.tech.level === 'gap');
  const total = requirements.reduce((acc, r) => acc + r.weight, 0);
  const covered = requirements.reduce((acc, r) => acc + r.weight * LEVEL_WEIGHT[r.tech.level], 0);
  return {
    requirements,
    matched,
    partial,
    missing,
    coverage: total === 0 ? 0 : Math.round((covered / total) * 100),
    role: detectRole(offer, requirements),
  };
}

const SKILLS_BY_ROLE: Record<Role, SkillsOrder> = {
  backend: 'backend_first',
  fullstack: 'fullstack',
  frontend: 'frontend_first',
};

export function joinEs(items: string[]): string {
  if (items.length <= 1) return items.join('');
  return `${items.slice(0, -1).join(', ')} y ${items[items.length - 1]}`;
}

export function topMatched(analysis: OfferAnalysis, count = 3): string[] {
  const names = analysis.matched
    .filter((r) => !['english', 'excel-csv', 'git'].includes(r.tech.id))
    .slice(0, count)
    .map((r) => r.tech.name);
  return names.length > 0 ? names : ['Java', 'Spring Boot', 'Angular'].slice(0, count);
}

function buildSummary(analysis: OfferAnalysis): string {
  const has = (id: string) => analysis.requirements.some((r) => r.tech.id === id);
  const key = topMatched(analysis, 3);
  const roleText: Record<Role, string> = {
    backend: 'backend',
    fullstack: 'full stack',
    frontend: 'frontend',
  };
  const s1 = `Desarrolladora ${roleText[analysis.role]} junior con experiencia real en ${joinEs(key)}, adquirida al llevar a producción un CRM comercial desarrollado de forma individual.`;
  const s2: Record<Role, string> = {
    backend:
      'Diseño APIs REST seguras (JWT, refresh tokens y RBAC con Spring Security) con persistencia en MySQL y PostgreSQL, arquitectura por capas y principios SOLID.',
    fullstack:
      'Cubro el ciclo completo: API REST segura con Spring Boot y cliente Angular/TypeScript responsive integrado contra ella.',
    frontend:
      'Construyo interfaces responsive con Angular, TypeScript, Bootstrap, HTML5 y CSS3 integradas con APIs REST y respaldadas por un backend Spring Boot propio.',
  };
  const extras: string[] = [];
  if (has('docker') || has('ci-cd') || has('cloud')) {
    extras.push('automatizo la entrega con Docker y GitHub Actions sobre un VPS real');
  }
  if (has('junit') || has('tdd')) extras.push('escribo pruebas con JUnit y Mockito');
  if (has('scrum')) extras.push('trabajo con metodologías ágiles (Scrum)');
  const s3 = extras.length > 0 ? `${capitalize(joinEs(extras))}. ` : '';
  const lang = 'Inglés C1 acreditado por la Universidad de Cambridge.';
  return `${s1} ${s2[analysis.role]} ${s3}${lang}`.replace(/\s+/g, ' ').trim();
}

function capitalize(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

export function tailorCv(profile: Profile, offer: OfferInput, description = ''): TailoredCv {
  const analysis = analyzeOffer(offer, description);
  const weightById = new Map(analysis.requirements.map((r) => [r.tech.id, r.weight] as const));

  const bullets: TailoredBullet[] = profile.bullets
    .map((b, originalIndex) => ({
      text: b.text,
      originalIndex,
      score: b.tags.reduce((acc, tag) => acc + (weightById.get(tag) ?? 0), 0),
    }))
    .sort((a, b) => b.score - a.score || a.originalIndex - b.originalIndex);

  const skillsOrder = SKILLS_BY_ROLE[analysis.role];
  const hitIds = new Set(analysis.requirements.map((r) => r.tech.id));
  const groups: TailoredGroup[] = profile.skills[skillsOrder].map((g: SkillGroup) => {
    const items = g.content.split(',').map((raw) => {
      const text = raw.trim();
      return { text, hit: detectTechs(text).some((t) => hitIds.has(t.id)) };
    });
    // Los términos que pide la oferta suben dentro de su bloque (mejor lectura ATS/humana).
    return { label: g.label, items: [...items.filter((i) => i.hit), ...items.filter((i) => !i.hit)] };
  });

  const topNames = topMatched(analysis, 3).map((n) => n.toUpperCase());
  return {
    analysis,
    title: `JUNIOR ${ROLE_LABEL[analysis.role]} · ${topNames.join(' · ')}`,
    summary: buildSummary(analysis),
    bullets,
    skillsOrder,
    groups,
  };
}
