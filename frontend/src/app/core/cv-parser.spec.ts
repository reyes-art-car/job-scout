import { parseCv } from './cv-parser';
import { parseProfile } from './profile-validation';

const CV = `
Ada Lovelace
Junior Full-Stack Developer
Sevilla, España
ada@example.com | linkedin.com/in/ada-lovelace | github.com/ada

PERFIL
Desarrolladora con ganas de aprender.

EXPERIENCIA
Desarrolladora Java/Angular - Acme
Marzo 2026 - Actualidad
CRM de gestión comercial en producción
• Puse en producción un CRM con Java, Spring Boot y Angular.
• Protegí el acceso con JWT y Spring Security
  con control de roles.
• Automaticé el despliegue con Docker y GitHub Actions.
Prácticas - Otra Empresa
2025 - 2026
• Tareas de soporte.

FORMACIÓN
Técnico Superior en Desarrollo de Aplicaciones Web
MEDAC 2024 - 2026

HABILIDADES
Java, Spring Boot, Angular, TypeScript, MySQL

IDIOMAS
Inglés C1
`;

describe('parseCv', () => {
  const profile = parseCv(CV);

  it('detecta los datos de contacto', () => {
    expect(profile.name).toBe('Ada Lovelace');
    expect(profile.title).toBe('Junior Full-Stack Developer');
    expect(profile.location).toBe('Sevilla, España');
    expect(profile.email).toBe('ada@example.com');
    expect(profile.linkedin).toBe('https://linkedin.com/in/ada-lovelace');
    expect(profile.github).toBe('https://github.com/ada');
  });

  it('toma solo el puesto más reciente, con su periodo y sus logros', () => {
    expect(profile.role).toBe('Desarrolladora Java/Angular');
    expect(profile.company).toBe('Acme');
    expect(profile.period).toBe('Marzo 2026 - Actualidad');
    expect(profile.project).toBe('CRM de gestión comercial en producción');
    expect(profile.bullets.length).toBe(3);
    expect(profile.bullets[1].text).toBe('Protegí el acceso con JWT y Spring Security con control de roles.');
  });

  it('etiqueta cada logro con las tecnologías del catálogo que menciona', () => {
    expect(profile.bullets[0].tags).toContain('java');
    expect(profile.bullets[0].tags).toContain('angular');
    expect(profile.bullets[2].tags).toContain('docker');
  });

  it('agrupa las tecnologías por categoría en los tres órdenes', () => {
    const labels = (order: keyof typeof profile.skills) => profile.skills[order].map((g) => g.label);
    expect(labels('backend_first')[0]).toBe('Backend');
    expect(labels('frontend_first')[0]).toBe('Frontend');
    expect(profile.skills.fullstack.some((g) => g.content.includes('Docker') || g.label === 'DevOps')).toBeTrue();
  });

  it('lee formación e idiomas', () => {
    expect(profile.education.degree).toBe('Técnico Superior en Desarrollo de Aplicaciones Web');
    expect(profile.education.school).toBe('MEDAC');
    expect(profile.education.years).toBe('2024 - 2026');
    expect(profile.languages.name).toBe('Inglés C1');
  });

  it('no inventa nada cuando el CV no tiene secciones reconocibles', () => {
    const bare = parseCv('Texto sin estructura que no menciona ninguna tecnología conocida en absoluto.');
    expect(bare.name).toBe('');
    expect(bare.bullets).toEqual([]);
    expect(bare.skills.fullstack).toEqual([]);
  });

  it('une la viñeta suelta con la línea siguiente', () => {
    const joined = parseCv('Ada Lovelace\nEXPERIENCIA\nDev - Acme\n2024 - 2025\n•\nTrabajé con Angular y TypeScript a diario.');
    expect(joined.bullets[0].text).toBe('Trabajé con Angular y TypeScript a diario.');
  });

  it('reconoce encabezados compuestos y el formato «EMPRESA | Puesto»', () => {
    const cv = parseCv(
      [
        'Ada Lovelace',
        'Sevilla, España | 600 000 000 | ada@example.com',
        'EXPERIENCIA Y PROYECTOS',
        'GRUPO ACME | Desarrolladora Java/Angular   Marzo 2026 - Actualidad',
        '• Diseñé la persistencia con Java, Spring Data JPA y SQL, con compatibilidad para MySQL y',
        'PostgreSQL, aplicando arquitectura por capas.',
        'COMPETENCIAS TÉCNICAS',
        'Java, Angular',
      ].join('\n'),
    );
    expect(cv.location).toBe('Sevilla, España');
    expect(cv.role).toBe('Desarrolladora Java/Angular');
    expect(cv.company).toBe('GRUPO ACME');
    expect(cv.bullets.length).toBe(1);
    expect(cv.bullets[0].text).toContain('MySQL y PostgreSQL');
  });

  it('separa titulación y centro escritos en la misma línea', () => {
    const cv = parseCv(['Ada Lovelace', 'FORMACIÓN', 'Técnico Superior en DAW | MEDAC Sevilla | 2024-2026'].join('\n'));
    expect(cv.education).toEqual({ degree: 'Técnico Superior en DAW', school: 'MEDAC Sevilla', years: '2024-2026' });
  });

  it('produce un perfil que supera la validación', () => {
    expect(parseProfile(profile)).not.toBeNull();
  });
});
