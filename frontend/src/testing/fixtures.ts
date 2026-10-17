import { Offer, Profile } from '../app/core/models';

export const PROFILE: Profile = {
  name: 'Ada Lovelace',
  title: 'Junior Full-Stack Developer',
  location: 'Sevilla, España',
  email: 'ada@example.com',
  linkedin: 'https://linkedin.com/in/ada',
  github: 'https://github.com/ada',
  company: 'Acme',
  role: 'Desarrolladora Java/Angular',
  period: '2026 - Actualidad',
  project: 'CRM',
  bullets: [
    { text: 'CRM en producción', tags: ['java', 'angular'] },
    { text: 'Seguridad con JWT', tags: ['jwt', 'spring-security'] },
    { text: 'CI/CD con Docker', tags: ['docker', 'ci-cd'] },
  ],
  skills: {
    backend_first: [{ label: 'Backend', content: 'Java, Spring Boot, JWT' }],
    fullstack: [{ label: 'Backend', content: 'Java, Spring Boot, JWT' }],
    frontend_first: [{ label: 'Frontend', content: 'Angular, TypeScript, Bootstrap' }],
  },
  education: { degree: 'DAW', school: 'MEDAC', years: '2024-2026' },
  languages: { name: 'Inglés C1', detail: 'Cambridge' },
};

export function offer(partial: Partial<Offer> = {}): Offer {
  return {
    id: 1,
    code: 'OF001',
    priority: 'Alta',
    compatibility: 80,
    title: 'Full Stack Developer',
    company: 'Empresa',
    portal: 'Tecnoempleo',
    url: null,
    published_date: '2026-10-16',
    location: 'España',
    modality: 'Remoto 100%',
    contract_type: 'Indefinido',
    salary: null,
    experience_required: '1-2 años',
    mandatory_tech: 'Java, Spring Boot, Angular',
    desirable_tech: 'Docker, Kafka',
    requirements_met: '',
    requirements_missing: '',
    score_reason: '',
    kanban_status: 'Pendiente',
    adapted_cv_filename: null,
    notes: null,
    source: 'legacy_excel',
    ...partial,
  };
}
