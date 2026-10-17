import { offer } from '../../testing/fixtures';
import { parseOffers, safeHttpUrl } from './offer-validation';

describe('safeHttpUrl', () => {
  it('acepta solo http y https', () => {
    expect(safeHttpUrl('https://example.com/a?b=1')).toBe('https://example.com/a?b=1');
    expect(safeHttpUrl('http://example.com')).toBe('http://example.com/');
  });

  it('rechaza esquemas peligrosos y valores no válidos', () => {
    for (const bad of ['javascript:alert(1)', 'JaVaScRiPt:alert(1)', 'data:text/html,x', 'file:///etc/passwd', 'ftp://x.com', '//evil.com', 'texto', '', null, 5, undefined]) {
      expect(safeHttpUrl(bad)).withContext(String(bad)).toBeNull();
    }
  });
});

describe('parseOffers', () => {
  it('devuelve null si no es una lista', () => {
    for (const bad of [null, undefined, {}, 'x', 5]) expect(parseOffers(bad)).toBeNull();
  });

  it('acepta una oferta válida sin cambios relevantes', () => {
    const [parsed] = parseOffers([offer({ url: 'https://example.com/x' })]) ?? [];
    expect(parsed.title).toBe('Full Stack Developer');
    expect(parsed.url).toBe('https://example.com/x');
  });

  it('descarta ofertas con forma inválida y conserva el resto', () => {
    const list = parseOffers([
      offer({ id: 1 }),
      { ...offer({ id: 2 }), kanban_status: 'Contratada' },
      { ...offer({ id: 3 }), compatibility: 250 },
      { ...offer({ id: 4 }), title: '' },
      { ...offer({ id: 5 }), id: 'cinco' },
      'basura',
      null,
    ]);
    expect(list?.map((o) => o.id)).toEqual([1]);
  });

  it('anula enlaces peligrosos en lugar de pasarlos a un href', () => {
    const [parsed] = parseOffers([offer({ url: 'javascript:alert(document.cookie)' })]) ?? [];
    expect(parsed.url).toBeNull();
  });

  it('recorta textos enormes y elimina campos desconocidos', () => {
    const hostile = { ...offer(), title: 'x'.repeat(10_000), __proto__: { admin: true }, extra: '<script>' };
    const [parsed] = parseOffers([hostile]) ?? [];
    expect(parsed.title.length).toBe(255);
    expect(Object.keys(parsed)).not.toContain('extra');
  });

  it('limita el número de ofertas', () => {
    const many = Array.from({ length: 6000 }, (_, i) => offer({ id: i + 1 }));
    expect(parseOffers(many)?.length).toBe(5000);
  });
});
