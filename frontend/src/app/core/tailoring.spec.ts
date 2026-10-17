import { offer, PROFILE } from '../../testing/fixtures';
import { analyzeOffer, extractRequirements, tailorCv } from './tailoring';

describe('analyzeOffer', () => {
  it('pondera más las obligatorias que las deseables', () => {
    const reqs = extractRequirements(offer());
    const java = reqs.find((r) => r.tech.id === 'java');
    const kafka = reqs.find((r) => r.tech.id === 'kafka');
    expect(java?.origin).toBe('obligatoria');
    expect(kafka?.origin).toBe('deseable');
    expect(java!.weight).toBeGreaterThan(kafka!.weight);
  });

  it('calcula cobertura 100 cuando todo está acreditado', () => {
    const a = analyzeOffer(offer({ mandatory_tech: 'Java, Spring Boot, Angular', desirable_tech: '' }));
    expect(a.coverage).toBe(100);
    expect(a.missing).toEqual([]);
  });

  it('lista las brechas y baja la cobertura', () => {
    const a = analyzeOffer(offer({ mandatory_tech: 'Java, Kafka, Kubernetes', desirable_tech: '' }));
    expect(a.missing.map((r) => r.tech.id).sort()).toEqual(['kafka', 'kubernetes']);
    expect(a.coverage).toBeLessThan(50);
  });

  it('detecta el rol a partir del título', () => {
    expect(analyzeOffer(offer({ title: 'Backend Java Developer' })).role).toBe('backend');
    expect(analyzeOffer(offer({ title: 'Frontend Engineer', mandatory_tech: 'Angular' })).role).toBe('frontend');
  });

  it('usa fullstack si no hay señales claras', () => {
    expect(analyzeOffer(offer({ title: 'Developer', mandatory_tech: '', desirable_tech: '' })).role).toBe('fullstack');
  });
});

describe('tailorCv', () => {
  it('sube los logros relevantes para la oferta', () => {
    const cv = tailorCv(PROFILE, offer({ title: 'Backend', mandatory_tech: 'Spring Security, JWT', desirable_tech: '' }));
    expect(cv.bullets[0].text).toBe('Seguridad con JWT');
    expect(cv.bullets.map((b) => b.originalIndex).sort()).toEqual([0, 1, 2]);
  });

  it('elige el orden de competencias según el rol', () => {
    expect(
      tailorCv(PROFILE, offer({ title: 'Frontend Developer', mandatory_tech: 'Angular, TypeScript' })).skillsOrder,
    ).toBe('frontend_first');
    expect(tailorCv(PROFILE, offer({ title: 'Backend Developer' })).skillsOrder).toBe('backend_first');
  });

  it('marca y adelanta las competencias que pide la oferta', () => {
    const cv = tailorCv(PROFILE, offer({ title: 'Backend', mandatory_tech: 'JWT', desirable_tech: '' }));
    expect(cv.groups[0].items[0]).toEqual({ text: 'JWT', hit: true });
  });

  it('el resumen nombra solo tecnologías que la candidata tiene', () => {
    const cv = tailorCv(PROFILE, offer({ mandatory_tech: 'Java, Kafka, Kubernetes, Angular' }));
    expect(cv.summary).toContain('Java');
    expect(cv.summary).not.toContain('Kafka');
    expect(cv.summary).not.toContain('Kubernetes');
    expect(cv.title).toContain('JUNIOR');
  });
});
