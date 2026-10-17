import { offer } from '../../testing/fixtures';
import { EMPTY_QUERY, applyQuery } from './offer-query';

const OFFERS = [
  offer({ id: 1, title: 'Java Dev', company: 'Zeta', compatibility: 70, kanban_status: 'Aplicado', published_date: '2026-10-01' }),
  offer({ id: 2, title: 'Angular Dev', company: 'Alfa', compatibility: 90, priority: 'Alta', published_date: '2026-10-10' }),
  offer({ id: 3, title: 'Backend', company: 'Beta', compatibility: 60, priority: 'Secundaria', mandatory_tech: 'Kafka', published_date: null }),
];

describe('applyQuery', () => {
  it('ordena por compatibilidad por defecto sin tocar la lista original', () => {
    expect(applyQuery(OFFERS, EMPTY_QUERY).map((o) => o.id)).toEqual([2, 1, 3]);
    expect(OFFERS.map((o) => o.id)).toEqual([1, 2, 3]);
  });

  it('busca en puesto, empresa y tecnologías sin distinguir mayúsculas', () => {
    expect(applyQuery(OFFERS, { ...EMPTY_QUERY, text: 'ALFA' }).map((o) => o.id)).toEqual([2]);
    expect(applyQuery(OFFERS, { ...EMPTY_QUERY, text: 'kafka' }).map((o) => o.id)).toEqual([3]);
  });

  it('filtra por estado, prioridad y compatibilidad mínima', () => {
    expect(applyQuery(OFFERS, { ...EMPTY_QUERY, status: 'Aplicado' }).map((o) => o.id)).toEqual([1]);
    expect(applyQuery(OFFERS, { ...EMPTY_QUERY, priority: 'Secundaria' }).map((o) => o.id)).toEqual([3]);
    expect(applyQuery(OFFERS, { ...EMPTY_QUERY, minCompatibility: 80 }).map((o) => o.id)).toEqual([2]);
  });

  it('ordena por fecha (las ofertas sin fecha al final) y por empresa', () => {
    expect(applyQuery(OFFERS, { ...EMPTY_QUERY, sort: 'fecha' }).map((o) => o.id)).toEqual([2, 1, 3]);
    expect(applyQuery(OFFERS, { ...EMPTY_QUERY, sort: 'empresa' }).map((o) => o.company)).toEqual(['Alfa', 'Beta', 'Zeta']);
  });
});
