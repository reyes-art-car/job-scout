import { CareerData, CvSnapshot, Evidence, SearchPreferences, SkillProgress, StatusEvent, safeEvidenceUrl } from './career';
import { Origin } from './offer-analysis';
import { TECH_CATALOG } from './tech-catalog';

const record = (v: unknown): v is Record<string, unknown> => !!v && typeof v === 'object' && !Array.isArray(v);
const text = (v: unknown, max: number): v is string => typeof v === 'string' && v.length <= max;
const nonempty = (v: unknown, max: number): v is string => text(v, max) && v.trim().length > 0;
const oneOf = (v: unknown, choices: string[]) => typeof v === 'string' && choices.includes(v);
const techIds = new Set(TECH_CATALOG.map(t => t.id));
const status = (v: unknown) => oneOf(v, ['Pendiente', 'Aplicado', 'Entrevista', 'Oferta', 'Rechazo']);
const date = (v: unknown) => typeof v === 'string' && /^\d{4}-\d{2}-\d{2}/.test(v) && Number.isFinite(Date.parse(v));
const safeUrl = (v: unknown): boolean => {
  if (!text(v, 2000)) return false;
  try { safeEvidenceUrl(v); return true; } catch { return false; }
};
function isEvidence(v: unknown): v is Evidence {
  if (!record(v)) return false;
  return text(v['id'], 100) && typeof v['techId'] === 'string' && techIds.has(v['techId']) &&
    nonempty(v['title'], 160) && nonempty(v['description'], 2000) && safeUrl(v['url']) && date(v['createdAt']);
}
function isProgress(v: unknown): v is SkillProgress {
  return record(v) && oneOf(v['stage'], ['pendiente', 'practicando', 'completado']) && oneOf(v['level'], ['have', 'partial', 'gap']);
}
function isPreferences(v: unknown): v is SearchPreferences {
  if (!record(v)) return false;
  const years = v['experienceYears'];
  return typeof years === 'number' && Number.isFinite(years) && years >= 0 && years <= 50 && text(v['location'], 160) && typeof v['remoteOnly'] === 'boolean';
}
function isEvent(v: unknown): v is StatusEvent {
  if (!record(v)) return false;
  return text(v['id'], 100) && text(v['offerKey'], 2000) && text(v['title'], 255) && text(v['company'], 255) && status(v['from']) && status(v['to']) && date(v['at']);
}
function isSnapshot(v: unknown): v is CvSnapshot {
  if (!record(v)) return false;
  const optionalDates = [v['appliedOn'], v['followUpOn']].every(d => d === null || date(d));
  return text(v['id'], 100) && text(v['offerKey'], 2000) && text(v['title'], 255) && text(v['company'], 255) && date(v['at']) && optionalDates && text(v['text'], 100000) && text(v['html'], 200000);
}
function arrayOf<T>(v: unknown, max: number, check: (item: unknown) => item is T): v is T[] {
  return Array.isArray(v) && v.length <= max && v.every(check);
}
function skillMap(v: unknown): v is Record<string, SkillProgress> {
  return record(v) && Object.entries(v).every(([id, progress]) => techIds.has(id) && isProgress(progress));
}
function correctionMap(v: unknown): v is Record<string, Record<string, Origin | 'ignorar'>> {
  if (!record(v) || Object.keys(v).length > 1000) return false;
  return Object.entries(v).every(([key, rows]) => key.length <= 2000 && record(rows) && Object.entries(rows).every(([id, origin]) => techIds.has(id) && oneOf(origin, ['obligatoria', 'deseable', 'texto', 'ignorar'])));
}
export function validateCareer(value: unknown): CareerData {
  if (!record(value) || value['version'] !== 1) throw new Error('Formato de copia de seguridad no compatible.');
  const { evidence, skills, corrections, preferences, events, snapshots } = value;
  if (!arrayOf(evidence, 1000, isEvidence)) throw new Error('Evidencias no válidas.');
  if (!skillMap(skills)) throw new Error('Progreso no válido.');
  if (!correctionMap(corrections)) throw new Error('Correcciones no válidas.');
  if (!isPreferences(preferences)) throw new Error('Preferencias no válidas.');
  if (!arrayOf(events, 5000, isEvent)) throw new Error('Historial no válido.');
  if (!arrayOf(snapshots, 300, isSnapshot)) throw new Error('Versiones de CV no válidas.');
  return JSON.parse(JSON.stringify({ version: 1, evidence, skills, corrections, preferences, events, snapshots })) as CareerData;
}
