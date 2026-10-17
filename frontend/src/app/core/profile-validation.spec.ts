import { PROFILE } from '../../testing/fixtures';
import { parseProfile } from './profile-validation';

describe('parseProfile', () => {
  it('acepta un perfil válido', () => {
    expect(parseProfile(PROFILE)?.name).toBe(PROFILE.name);
  });

  it('rechaza lo que no es un objeto o no tiene nombre', () => {
    expect(parseProfile(null)).toBeNull();
    expect(parseProfile([])).toBeNull();
    expect(parseProfile({ ...PROFILE, name: '   ' })).toBeNull();
  });

  it('rechaza un perfil sin tecnologías ni logros', () => {
    expect(parseProfile({ ...PROFILE, bullets: [], skills: { backend_first: [], fullstack: [], frontend_first: [] } })).toBeNull();
  });

  it('descarta enlaces peligrosos y etiquetas desconocidas', () => {
    const profile = parseProfile({
      ...PROFILE,
      linkedin: 'javascript:alert(1)',
      github: 'https://github.com/ada',
      bullets: [{ text: 'Logro', tags: ['java', 'no-existe', 42] }],
    });
    expect(profile?.linkedin).toBe('');
    expect(profile?.github).toBe('https://github.com/ada');
    expect(profile?.bullets[0].tags).toEqual(['java']);
  });

  it('limita la longitud de los textos y el número de logros', () => {
    const profile = parseProfile({
      ...PROFILE,
      name: 'x'.repeat(1000),
      bullets: Array.from({ length: 100 }, (_, i) => ({ text: `Logro ${i}`, tags: [] })),
    });
    expect(profile?.name.length).toBe(160);
    expect(profile?.bullets.length).toBe(30);
  });
});
