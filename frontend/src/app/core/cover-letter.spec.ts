import { offer, PROFILE } from '../../testing/fixtures';
import { DEFAULT_LETTER_OPTIONS, buildCoverLetter, letterToText } from './cover-letter';

describe('buildCoverLetter', () => {
  it('incluye puesto, empresa y portal en el asunto y la introducción', () => {
    const letter = buildCoverLetter(PROFILE, offer({ title: 'Java Developer', company: 'Acme SL' }));
    expect(letter.subject).toContain('Java Developer');
    expect(letter.paragraphs[0]).toContain('Acme SL');
    expect(letter.paragraphs[0]).toContain('Tecnoempleo');
  });

  it('menciona modalidad remota solo si la oferta es remota', () => {
    const remote = buildCoverLetter(PROFILE, offer({ modality: 'Remoto 100%' }));
    const hybrid = buildCoverLetter(PROFILE, offer({ modality: 'Híbrido' }));
    expect(remote.closing).toContain('100% remota');
    expect(hybrid.closing).not.toContain('remota');
  });

  it('añade el párrafo de brechas solo cuando se pide', () => {
    const o = offer({ mandatory_tech: 'Java, Kafka' });
    const without = buildCoverLetter(PROFILE, o, DEFAULT_LETTER_OPTIONS);
    const withGaps = buildCoverLetter(PROFILE, o, { ...DEFAULT_LETTER_OPTIONS, mentionGaps: true });
    expect(without.paragraphs.join(' ')).not.toContain('Kafka');
    expect(withGaps.paragraphs.join(' ')).toContain('Kafka');
  });

  it('no inventa tecnologías en la carta por defecto', () => {
    const text = buildCoverLetter(PROFILE, offer({ mandatory_tech: 'Java, React, AWS' })).paragraphs.join(' ');
    expect(text).not.toContain('React');
    expect(text).not.toContain('AWS');
  });

  it('serializa la carta con fecha y firma', () => {
    const letter = buildCoverLetter(PROFILE, offer());
    const text = letterToText(letter, 'Empresa', 'Sevilla, 1 de enero de 2027');
    expect(text).toContain('Sevilla, 1 de enero de 2027');
    expect(text.trim().endsWith(PROFILE.name)).toBeTrue();
  });
});
