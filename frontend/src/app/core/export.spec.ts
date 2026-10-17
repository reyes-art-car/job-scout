import { offer } from '../../testing/fixtures';
import { offersToCsv, slug } from './export';

describe('offersToCsv', () => {
  it('empieza con BOM UTF-8 y separa con punto y coma', () => {
    const csv = offersToCsv([offer()]);
    expect(csv.charCodeAt(0)).toBe(0xfeff);
    expect(csv.split('\r\n')[0]).toContain('"ID";"Prioridad"');
    expect(csv.split('\r\n')).toHaveSize(2);
  });

  it('escapa comillas y neutraliza fórmulas', () => {
    const csv = offersToCsv([offer({ title: 'Dev "Senior"', notes: '=HYPERLINK("x")' })]);
    expect(csv).toContain('"Dev ""Senior"""');
    expect(csv).toContain('"\'=HYPERLINK(""x"")"');
  });
});

describe('slug', () => {
  it('quita tildes y símbolos', () => {
    expect(slug('Ingeniería & Software!')).toBe('IngenieriaSoftware');
  });
});
