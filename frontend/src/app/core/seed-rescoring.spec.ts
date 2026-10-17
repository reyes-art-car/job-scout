import { offer, PROFILE } from '../../testing/fixtures';
import { emptyCareer } from './career';
import { rescoreSeed } from './seed-rescoring';

describe('rescoreSeed', () => {
  const seed = offer({
    compatibility: 10,
    priority: 'Secundaria',
    kanban_status: 'Entrevista',
    notes: 'Nota privada de otra persona',
    mandatory_tech: 'Java, Spring Boot, Angular',
    desirable_tech: 'Kafka',
  });

  it('recalcula la compatibilidad con el perfil de la persona', () => {
    const [scored] = rescoreSeed([seed], PROFILE, emptyCareer());
    expect(scored.compatibility).toBeGreaterThan(50);
    expect(scored.priority).toBe(scored.compatibility >= 75 ? 'Alta' : 'Secundaria');
    expect(scored.requirements_met).toContain('Java');
  });

  it('puntúa menos a un perfil sin esas tecnologías', () => {
    const empty = { ...PROFILE, bullets: [], skills: { backend_first: [], fullstack: [], frontend_first: [] } };
    const [mine] = rescoreSeed([seed], PROFILE, emptyCareer());
    const [other] = rescoreSeed([seed], empty, emptyCareer());
    expect(other.compatibility).toBeLessThan(mine.compatibility);
  });

  it('limpia el estado y las notas de quien revisó el ejemplo', () => {
    const [scored] = rescoreSeed([seed], PROFILE, emptyCareer());
    expect(scored.kanban_status).toBe('Pendiente');
    expect(scored.notes).toBeNull();
  });
});
