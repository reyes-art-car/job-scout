import { Profile, ProfileBullet, SkillGroup, SkillsOrder } from './models';
import { TECH_CATALOG } from './tech-catalog';
import { safeHttpUrl } from './offer-validation';

const SHORT = 160;
const LONG = 600;
const MAX_BULLETS = 30;
const MAX_GROUPS = 12;

const ORDERS: readonly SkillsOrder[] = ['backend_first', 'fullstack', 'frontend_first'];
const TECH_IDS = new Set(TECH_CATALOG.map((t) => t.id));

type Raw = Record<string, unknown>;

const isRecord = (value: unknown): value is Raw => typeof value === 'object' && value !== null && !Array.isArray(value);

function text(raw: Raw, key: string, limit = SHORT): string {
  const value = raw[key];
  return typeof value === 'string' ? value.replace(/\s+/g, ' ').trim().slice(0, limit) : '';
}

function link(raw: Raw, key: string): string {
  const value = raw[key];
  return typeof value === 'string' && value.trim() !== '' ? (safeHttpUrl(value.trim()) ?? '') : '';
}

function bullets(value: unknown): ProfileBullet[] {
  if (!Array.isArray(value)) return [];
  return value
    .slice(0, MAX_BULLETS)
    .filter(isRecord)
    .map((b) => ({
      text: text(b, 'text', LONG),
      tags: Array.isArray(b['tags']) ? b['tags'].filter((t): t is string => typeof t === 'string' && TECH_IDS.has(t)) : [],
    }))
    .filter((b) => b.text !== '');
}

function groups(value: unknown): SkillGroup[] {
  if (!Array.isArray(value)) return [];
  return value
    .slice(0, MAX_GROUPS)
    .filter(isRecord)
    .map((g) => ({ label: text(g, 'label'), content: text(g, 'content', LONG) }))
    .filter((g) => g.label !== '' && g.content !== '');
}

/**
 * Valida un perfil que viene de fuera (localStorage o el formulario de importación). Devuelve `null` si no es
 * utilizable: sin nombre o sin ninguna tecnología/logro no hay nada que analizar.
 */
export function parseProfile(value: unknown): Profile | null {
  if (!isRecord(value)) return null;
  const name = text(value, 'name');
  const skills = isRecord(value['skills']) ? value['skills'] : {};
  const education = isRecord(value['education']) ? value['education'] : {};
  const languages = isRecord(value['languages']) ? value['languages'] : {};
  const parsedSkills = Object.fromEntries(ORDERS.map((o) => [o, groups(skills[o])])) as Record<SkillsOrder, SkillGroup[]>;
  const parsedBullets = bullets(value['bullets']);
  const hasSkills = ORDERS.some((o) => parsedSkills[o].length > 0);
  if (!name || (!hasSkills && parsedBullets.length === 0)) return null;
  return {
    name,
    title: text(value, 'title'),
    location: text(value, 'location'),
    email: text(value, 'email'),
    linkedin: link(value, 'linkedin'),
    github: link(value, 'github'),
    company: text(value, 'company'),
    role: text(value, 'role'),
    period: text(value, 'period'),
    project: text(value, 'project', LONG),
    bullets: parsedBullets,
    skills: parsedSkills,
    education: { degree: text(education, 'degree'), school: text(education, 'school'), years: text(education, 'years', 40) },
    languages: { name: text(languages, 'name'), detail: text(languages, 'detail') },
  };
}
