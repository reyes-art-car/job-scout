import { KanbanStatus } from './models';

const HIGH = 80;
const MID = 70;

export type ScoreTone = 'high' | 'mid' | 'low';

export const scoreTone = (score: number): ScoreTone => (score >= HIGH ? 'high' : score >= MID ? 'mid' : 'low');

const STATUS_CHIP: Record<KanbanStatus, string> = {
  Pendiente: '',
  Aplicado: 'info',
  Entrevista: 'accent',
  Oferta: 'ok',
  Rechazo: 'bad',
};

export const statusChipClass = (status: KanbanStatus): string => STATUS_CHIP[status];
