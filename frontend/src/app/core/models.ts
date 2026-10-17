export type KanbanStatus = 'Pendiente' | 'Aplicado' | 'Entrevista' | 'Oferta' | 'Rechazo';
export type Priority = 'Alta' | 'Secundaria';
export type SkillsOrder = 'backend_first' | 'fullstack' | 'frontend_first';

export const KANBAN_STATUSES: readonly KanbanStatus[] = [
  'Pendiente',
  'Aplicado',
  'Entrevista',
  'Oferta',
  'Rechazo',
] as const;

/** Umbral de la rúbrica de búsqueda: ≥ 75 % → prioridad alta (igual que el backend). */
export const HIGH_PRIORITY_THRESHOLD = 75;

export const priorityFor = (compatibility: number): Priority =>
  compatibility >= HIGH_PRIORITY_THRESHOLD ? 'Alta' : 'Secundaria';

/** Misma forma que `OfferOut` del backend (snake_case) para poder usar la API o el modo demo sin mapeos. */
export interface Offer {
  id: number;
  code: string;
  priority: Priority;
  compatibility: number;
  title: string;
  company: string;
  portal: string;
  url: string | null;
  published_date: string | null;
  location: string;
  modality: string;
  contract_type: string;
  salary: string | null;
  experience_required: string;
  mandatory_tech: string;
  desirable_tech: string;
  requirements_met: string;
  requirements_missing: string;
  score_reason: string;
  kanban_status: KanbanStatus;
  adapted_cv_filename: string | null;
  notes: string | null;
  source: string;
}

export type NewOffer = Omit<Offer, 'id' | 'code' | 'priority' | 'adapted_cv_filename' | 'source'> &
  Partial<Pick<Offer, 'priority'>>;

export interface SkillGroup {
  label: string;
  content: string;
}

export interface ProfileBullet {
  text: string;
  /** Ids del catálogo de tecnologías que acredita este logro. */
  tags: string[];
}

export interface Profile {
  name: string;
  title: string;
  location: string;
  email: string;
  linkedin: string;
  github: string;
  company: string;
  role: string;
  period: string;
  project: string;
  bullets: ProfileBullet[];
  skills: Record<SkillsOrder, SkillGroup[]>;
  education: { degree: string; school: string; years: string };
  languages: { name: string; detail: string };
}
