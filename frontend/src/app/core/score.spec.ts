import { scoreTone, statusChipClass } from './score';

describe('score', () => {
  it('clasifica la compatibilidad en tres tramos', () => {
    expect([95, 80, 79, 70, 69, 0].map(scoreTone)).toEqual(['high', 'high', 'mid', 'mid', 'low', 'low']);
  });

  it('asigna una clase a cada estado', () => {
    expect(statusChipClass('Oferta')).toBe('ok');
    expect(statusChipClass('Rechazo')).toBe('bad');
    expect(statusChipClass('Pendiente')).toBe('');
  });
});
