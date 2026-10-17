import { KanbanStatus, Offer, Profile } from './models';
import { Origin, Requirement, analyzeOffer } from './offer-analysis';
import { TECH_CATALOG, TechLevel, detectTechs } from './tech-catalog';

export type LearningStage = 'pendiente' | 'practicando' | 'completado';
export interface Evidence { id: string; techId: string; title: string; description: string; url: string; createdAt: string }
export interface SkillProgress { stage: LearningStage; level: TechLevel }
export interface SearchPreferences { experienceYears: number; location: string; remoteOnly: boolean }
export interface StatusEvent { id: string; offerKey: string; title: string; company: string; from: KanbanStatus; to: KanbanStatus; at: string }
export interface CvSnapshot { id: string; offerKey: string; title: string; company: string; at: string; appliedOn: string | null; followUpOn: string | null; text: string; html: string }
export interface CareerData {
  version: 1;
  evidence: Evidence[];
  skills: Record<string, SkillProgress>;
  corrections: Record<string, Record<string, Origin | 'ignorar'>>;
  preferences: SearchPreferences;
  events: StatusEvent[];
  snapshots: CvSnapshot[];
}
export const emptyCareer = (): CareerData => ({
  version: 1, evidence: [], skills: {}, corrections: {},
  preferences: { experienceYears: 0, location: '', remoteOnly: false }, events: [], snapshots: []
});
export const offerKey = (offer: Offer, mode: string): string => `${mode}:${offer.code}:${offer.url ?? offer.id}`;
export function safeEvidenceUrl(value: string): string {
  if (!value.trim()) return '';
  const url = new URL(value);
  if (!['https:', 'http:'].includes(url.protocol) || url.username || url.password) throw new Error('Usa un enlace http o https sin credenciales.');
  return url.href;
}
export function profileLevels(profile: Profile, data: CareerData): Record<string, TechLevel> {
  const text = [...Object.values(profile.skills).flat().map(g => g.content), profile.languages.name].join(' ');
  const declared = new Set(detectTechs(text).map(t => t.id));
  for (const bullet of profile.bullets) for (const id of bullet.tags) declared.add(id);
  return Object.fromEntries(TECH_CATALOG.map(tech => {
    const saved = data.skills[tech.id];
    const evidenced = data.evidence.some(e => e.techId === tech.id);
    const level = saved?.level === 'have' && !evidenced ? 'partial' : saved?.level;
    return [tech.id, level ?? (declared.has(tech.id) ? 'have' : 'gap')];
  }));
}
export function evidenceSources(profile: Profile, data: CareerData, techId: string): string[] {
  const sources = data.evidence.filter(e => e.techId === techId).map(e => `${e.title}: ${e.description}`);
  for (const bullet of profile.bullets) if (bullet.tags.includes(techId)) sources.push(`Logro del perfil: ${bullet.text}`);
  if (!sources.length && detectTechs(Object.values(profile.skills).flat().map(g => g.content).join(' ')).some(t => t.id === techId)) {
    sources.push('Competencia declarada en el perfil; añade un proyecto o certificado para respaldarla.');
  }
  if (techId === 'english') sources.push(`${profile.languages.name}: ${profile.languages.detail}`);
  return sources;
}
export function explainedRequirements(offer: Offer, description: string, levels: Record<string, TechLevel>, corrections: Record<string, Origin | 'ignorar'>): Requirement[] {
  return analyzeOffer(offer, description, levels).requirements.flatMap(r => {
    const correction = corrections[r.tech.id];
    if (correction === 'ignorar') return [];
    const origin = correction ?? r.origin;
    return [{ ...r, origin, weight: r.tech.id === 'english' ? 0.5 : ({ obligatoria: 3, texto: 1.5, deseable: 1 })[origin] }];
  });
}
export function coverageOf(requirements: Requirement[]): number {
  const total = requirements.reduce((sum, r) => sum + r.weight, 0);
  const covered = requirements.reduce((sum, r) => sum + r.weight * ({ have: 1, partial: 0.5, gap: 0 })[r.tech.level], 0);
  return total ? Math.round(100 * covered / total) : 0;
}
export interface FitWarning { kind: 'experience' | 'seniority' | 'location' | 'remote' | 'unknown'; text: string }
export function fitWarnings(offer: Offer, preferences: SearchPreferences): FitWarning[] {
  const warnings: FitWarning[] = [];
  const experience = offer.experience_required.toLowerCase();
  if (/\b(senior|sr\.?|lead|principal)\b/i.test(offer.title) && preferences.experienceYears < 3) warnings.push({ kind: 'seniority', text: 'El título apunta a un puesto con experiencia. Comprueba el alcance aunque haya coincidencia técnica.' });
  const matches = [...experience.matchAll(/(\d+)\s*(?:[-–a]|o)?\s*(?:\d+)?\s*(?:años?|years?)/g)];
  const years = matches.length ? Math.max(...matches.map(m => Number(m[1]))) : null;
  if (years !== null && years > preferences.experienceYears) warnings.push({ kind: 'experience', text: `Pide al menos ${years} años; has indicado ${preferences.experienceYears}. Confirma si es imprescindible.` });
  if (years === null) warnings.push({ kind: 'unknown', text: 'Experiencia mínima sin confirmar. Revisa el anuncio original.' });
  const remote = /remot|teletrabaj/.test(offer.modality.toLowerCase());
  if (preferences.remoteOnly && !remote) warnings.push({ kind: 'remote', text: 'Buscas remoto y la modalidad no lo confirma.' });
  if (preferences.location.trim() && !offer.location.toLowerCase().includes(preferences.location.toLowerCase())) {
    warnings.push({ kind: 'location', text: `La ubicación no coincide con ${preferences.location}. El trabajo remoto puede tener restricciones territoriales.` });
  }
  return warnings;
}
export function followUpDate(appliedOn: string): string {
  const date = new Date(`${appliedOn}T12:00:00Z`);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(appliedOn) || Number.isNaN(date.getTime()) || date.toISOString().slice(0, 10) !== appliedOn) throw new Error('La fecha de envío no es válida.');
  date.setUTCDate(date.getUTCDate() + 7);
  return date.toISOString().slice(0, 10);
}

export function analyzeForCareer(profile: Profile, data: CareerData, offer: Offer, mode: string, description = '') {
  const levels = profileLevels(profile, data);
  const requirements = explainedRequirements(offer, description, levels, data.corrections[offerKey(offer, mode)] ?? {});
  return analyzeOffer(offer, description, levels, requirements);
}

export function enrichedProfile(profile: Profile, data: CareerData): Profile {
  const confirmed = data.evidence.filter(e => data.skills[e.techId]?.level === 'have');
  const names = [...new Set(confirmed.map(e => TECH_CATALOG.find(t => t.id === e.techId)?.name).filter((n): n is string => !!n))];
  const group = { label: 'Competencias respaldadas por evidencias', content: names.join(', ') };
  const bullets = profile.bullets.filter(b => !b.tags.some(id => data.skills[id] && data.skills[id].level !== 'have'));
  return {
    ...profile, bullets: [...bullets, ...confirmed.map(e => ({ text: `${e.title}: ${e.description}`, tags: [e.techId] }))],
    skills: { backend_first: [...profile.skills.backend_first, ...(names.length ? [group] : [])], fullstack: [...profile.skills.fullstack, ...(names.length ? [group] : [])], frontend_first: [...profile.skills.frontend_first, ...(names.length ? [group] : [])] }
  };
}
