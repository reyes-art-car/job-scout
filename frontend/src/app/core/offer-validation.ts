import { KANBAN_STATUSES, KanbanStatus, Offer, Priority } from './models';

const MAX_OFFERS = 5000;
const SHORT = 255;
const LONG = 4000;

const PRIORITIES: readonly Priority[] = ['Alta', 'Secundaria'];

type Raw = Record<string, unknown>;

const isRecord = (value: unknown): value is Raw => typeof value === 'object' && value !== null && !Array.isArray(value);

function text(raw: Raw, key: string, limit = SHORT): string {
  const value = raw[key];
  return typeof value === 'string' ? value.slice(0, limit) : '';
}

function optionalText(raw: Raw, key: string, limit = SHORT): string | null {
  const value = raw[key];
  return typeof value === 'string' && value !== '' ? value.slice(0, limit) : null;
}

/** Solo enlaces http(s): bloquea `javascript:`, `data:` y similares antes de que lleguen a un `href`. */
export function safeHttpUrl(value: unknown): string | null {
  if (typeof value !== 'string') return null;
  try {
    const url = new URL(value);
    return url.protocol === 'http:' || url.protocol === 'https:' ? url.href : null;
  } catch {
    return null;
  }
}

function parseOffer(value: unknown): Offer | null {
  if (!isRecord(value)) return null;
  const id = value['id'];
  const compatibility = value['compatibility'];
  const status = value['kanban_status'];
  const priority = value['priority'];
  if (typeof id !== 'number' || !Number.isInteger(id)) return null;
  if (typeof compatibility !== 'number' || compatibility < 0 || compatibility > 100) return null;
  if (!KANBAN_STATUSES.includes(status as KanbanStatus)) return null;
  const title = text(value, 'title');
  const company = text(value, 'company');
  if (!title || !company) return null;

  return {
    id,
    code: text(value, 'code', 16),
    priority: PRIORITIES.includes(priority as Priority) ? (priority as Priority) : 'Secundaria',
    compatibility: Math.round(compatibility),
    title,
    company,
    portal: text(value, 'portal'),
    url: safeHttpUrl(value['url']),
    published_date: optionalText(value, 'published_date', 10),
    location: text(value, 'location'),
    modality: text(value, 'modality', 100),
    contract_type: text(value, 'contract_type', 100),
    salary: optionalText(value, 'salary'),
    experience_required: text(value, 'experience_required'),
    mandatory_tech: text(value, 'mandatory_tech', LONG),
    desirable_tech: text(value, 'desirable_tech', LONG),
    requirements_met: text(value, 'requirements_met', LONG),
    requirements_missing: text(value, 'requirements_missing', LONG),
    score_reason: text(value, 'score_reason', LONG),
    kanban_status: status as KanbanStatus,
    adapted_cv_filename: optionalText(value, 'adapted_cv_filename'),
    notes: optionalText(value, 'notes', LONG),
    source: text(value, 'source', 30),
  };
}

/**
 * Valida y normaliza una lista de ofertas llegada de la red o de `localStorage`.
 * Devuelve `null` si la estructura no es una lista: así datos manipulados nunca rompen la app ni
 * llegan a la plantilla con un formato inesperado.
 */
export function parseOffers(value: unknown): Offer[] | null {
  if (!Array.isArray(value)) return null;
  return value
    .slice(0, MAX_OFFERS)
    .map(parseOffer)
    .filter((offer): offer is Offer => offer !== null);
}
