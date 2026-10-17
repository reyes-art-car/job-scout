import { Profile, SkillGroup, SkillsOrder } from './models';
import { OfferAnalysis, OfferInput, Role, analyzeOffer, topMatched } from './offer-analysis';
import { capitalize, joinEs } from './text';
import { detectTechs } from './tech-catalog';

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

const ROLE_LABEL: Record<Role, string> = {
  backend: 'JAVA BACKEND DEVELOPER',
  fullstack: 'FULL STACK DEVELOPER',
  frontend: 'FRONTEND DEVELOPER',
};

const SKILLS_BY_ROLE: Record<Role, SkillsOrder> = {
  backend: 'backend_first',
  fullstack: 'fullstack',
  frontend: 'frontend_first',
};

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
