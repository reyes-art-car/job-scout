import { Profile, ProfileBullet, SkillGroup, SkillsOrder } from './models';
import { Tech, TechCategory, detectTechs } from './tech-catalog';

type Section = 'header' | 'profile' | 'experience' | 'education' | 'skills' | 'languages' | 'projects' | 'other';

const HEADINGS: Record<Exclude<Section, 'header' | 'other'>, RegExp> = {
  profile: /^(perfil(?: profesional)?|sobre m[ií]|resumen(?: profesional)?|summary|profile|about me|objetivo(?: profesional)?)(?!\p{L})/iu,
  experience: /^(experiencia(?: laboral| profesional)?|experience|work experience|professional experience|employment|trayectoria profesional)(?!\p{L})/iu,
  education: /^(educaci[oó]n|formaci[oó]n(?: acad[eé]mica)?|estudios|education|titulaci[oó]n)(?!\p{L})/iu,
  skills: /^(habilidades|competencias|skills|tecnolog[ií]as|conocimientos(?: t[eé]cnicos)?|technical skills|aptitudes|stack(?: t[eé]cnico)?)(?!\p{L})/iu,
  languages: /^(idiomas|languages)(?!\p{L})/iu,
  projects: /^(proyectos(?: personales)?|projects)(?!\p{L})/iu,
};
/** Otros encabezados habituales: sirven para cerrar la sección anterior sin mezclar su contenido. */
const OTHER_HEADING =
  /^(certificaciones|certificados|cursos|intereses|aficiones|referencias|datos personales|informaci[oó]n adicional|voluntariado|publicaciones|certifications|interests|references|awards|premios)$/i;

const BULLET = /^[•·▪●◦■□➢✓✔➔►*–—-]\s*/;
const GLYPH_ONLY = /^[•·▪●◦■□➢✓✔➔►*]$/;
const MONTH = '(?:(?:ene|feb|mar|abr|may|jun|jul|ago|sep|set|oct|nov|dic|jan|apr|aug|dec)[a-záéíóú]*\\.?\\s+)?';
const PERIOD = new RegExp(`${MONTH}\\d{4}\\s*(?:-|–|—|a|hasta|to)\\s*(?:actualidad|presente|present|current|hoy|${MONTH}\\d{4})`, 'i');
const EMAIL = /[\w.+-]+@[\w-]+(?:\.[\w-]+)+/;
const LINKEDIN = /(?:https?:\/\/)?(?:[a-z]{2,3}\.)?linkedin\.com\/in\/[\w%-]+/i;
const GITHUB = /(?:https?:\/\/)?(?:www\.)?github\.com\/[\w-]+/i;
const ROLE_WORD = /(desarrollador|developer|engineer|ingenier|programador|analista|arquitect|devops|full.?stack|backend|frontend|qa|tester|data|consultor)/i;

const CATEGORY_ORDER: Record<SkillsOrder, TechCategory[]> = {
  backend_first: ['Backend', 'Datos', 'Arquitectura', 'Mensajería', 'DevOps', 'Cloud', 'Calidad', 'Frontend', 'IA', 'Metodología', 'Otros'],
  fullstack: ['Backend', 'Frontend', 'Datos', 'Arquitectura', 'Mensajería', 'DevOps', 'Cloud', 'Calidad', 'IA', 'Metodología', 'Otros'],
  frontend_first: ['Frontend', 'Backend', 'Datos', 'Arquitectura', 'Calidad', 'DevOps', 'Cloud', 'Mensajería', 'IA', 'Metodología', 'Otros'],
};

const MAX_BULLETS = 12;
const MAX_HEADER_LINES = 4;

function cleanLines(raw: string): string[] {
  const lines = raw
    .replace(/\r/g, '')
    .split('\n')
    .map((l) => l.replace(/\s+/g, ' ').trim())
    .filter((l) => l !== '');
  // Algunos PDF extraen la viñeta en una línea y el texto en la siguiente.
  const merged: string[] = [];
  for (let i = 0; i < lines.length; i++) {
    if (GLYPH_ONLY.test(lines[i]) && i + 1 < lines.length) {
      merged.push(`• ${lines[i + 1]}`);
      i++;
    } else merged.push(lines[i]);
  }
  return merged;
}

function headingOf(line: string): Section | null {
  const normalized = line.replace(/^[^\p{L}]+|[^\p{L}]+$/gu, '').trim();
  // Un encabezado es corto y sin datos: así «Experiencia y proyectos» cuenta, pero «Experiencia en Java: 3 años» no.
  if (normalized.length === 0 || normalized.length > 40 || normalized.split(' ').length > 4 || /[\d|·@:]/.test(line.replace(/[:：]\s*$/, ''))) return null;
  for (const [section, regex] of Object.entries(HEADINGS)) if (regex.test(normalized)) return section as Section;
  return OTHER_HEADING.test(normalized) ? 'other' : null;
}

function splitSections(lines: string[]): Record<Section, string[]> {
  const sections: Record<Section, string[]> = { header: [], profile: [], experience: [], education: [], skills: [], languages: [], projects: [], other: [] };
  let current: Section = 'header';
  for (const line of lines) {
    const heading = headingOf(line);
    if (heading) current = heading;
    else sections[current].push(line);
  }
  return sections;
}

const withProtocol = (url: string): string => (/^https?:\/\//i.test(url) ? url : `https://${url}`);

function looksLikeName(line: string): boolean {
  const words = line.split(' ');
  return (
    words.length >= 2 &&
    words.length <= 6 &&
    line.length <= 60 &&
    !/[\d@/:]/.test(line) &&
    !ROLE_WORD.test(line) &&
    words.every((w) => /^[\p{L}'.-]+$/u.test(w))
  );
}

function parseHeader(lines: string[], full: string): Pick<Profile, 'name' | 'title' | 'location' | 'email' | 'linkedin' | 'github'> {
  const top = lines.slice(0, 12);
  const name = top.find(looksLikeName) ?? '';
  // Los datos de contacto suelen ir en una sola línea separados por «|» o «·»: se busca la localidad en cada tramo.
  const title = (top.find((l) => l !== name && ROLE_WORD.test(l) && l.length <= 120 && !EMAIL.test(l)) ?? '').split('|')[0].trim();
  const location =
    top
      .flatMap((l) => l.split(/\s*[|·•]\s*/))
      .find((part) => /^\p{Lu}[\p{L} .'-]+,\s*\p{Lu}[\p{L} .'-]+$/u.test(part) && part.length <= 60 && part !== name && part !== title) ?? '';
  const linkedin = LINKEDIN.exec(full)?.[0];
  const github = GITHUB.exec(full)?.[0];
  return {
    name,
    title,
    location,
    email: EMAIL.exec(full)?.[0] ?? '',
    linkedin: linkedin ? withProtocol(linkedin) : '',
    github: github ? withProtocol(github) : '',
  };
}

interface RawExperience {
  header: string[];
  bullets: ProfileBullet[];
  period: string;
}

/** Recorre la sección: líneas de cabecera del puesto, periodo y viñetas del primer puesto (el más reciente). */
function scanExperience(lines: string[]): RawExperience {
  const raw: RawExperience = { header: [], bullets: [], period: '' };
  for (const line of lines) {
    const periodMatch = PERIOD.exec(line);
    // Un segundo periodo indica otro puesto: solo se importa el primero del CV.
    if (periodMatch && raw.bullets.length > 0) break;
    if (BULLET.test(line)) raw.bullets.push({ text: line.replace(BULLET, ''), tags: [] });
    else if (raw.bullets.length > 0) appendOrAdd(raw.bullets, line);
    else if (periodMatch) addPeriodLine(raw, line, periodMatch[0]);
    else if (raw.header.length < MAX_HEADER_LINES && line.length <= 90) raw.header.push(line);
    else if (line.length >= 40) raw.bullets.push({ text: line, tags: [] });
  }
  return raw;
}

function appendOrAdd(bullets: ProfileBullet[], line: string): void {
  // Una línea que sigue a una viñeta sin cerrar (o que continúa en minúscula) es parte de ella; si no, las frases largas son logros.
  const last = bullets[bullets.length - 1];
  if (/^\p{Ll}/u.test(line) || !/[.!?;:]$/.test(last.text)) last.text += ` ${line}`;
  else if (line.length >= 40) bullets.push({ text: line, tags: [] });
}

function addPeriodLine(raw: RawExperience, line: string, period: string): void {
  raw.period ||= period;
  const rest = line.replace(PERIOD, '').replace(/^[\s|·,–—-]+|[\s|·,–—-]+$/g, '');
  if (rest && raw.header.length < MAX_HEADER_LINES) raw.header.push(rest);
}

function parseExperience(lines: string[]): Pick<Profile, 'company' | 'role' | 'period' | 'project' | 'bullets'> {
  const { header, bullets, period } = scanExperience(lines);
  const [first = '', second = '', third = ''] = header;
  const split = first.split(/\s+(?:[-–—|·]|en|at|@)\s+/);
  // «EMPRESA | Puesto» y «Puesto - Empresa» son igual de habituales: gana el tramo que suena a puesto.
  const swapped = split.length > 1 && !ROLE_WORD.test(split[0]) && ROLE_WORD.test(split[split.length - 1]);
  const role = swapped ? split[split.length - 1] : (split[0] ?? '');
  const company = split.length > 1 ? (swapped ? split.slice(0, -1) : split.slice(1)).join(' · ') : second;
  const project = split.length > 1 ? second : third;
  return {
    company: company.slice(0, 160),
    role: role.slice(0, 160),
    period,
    project: project.slice(0, 600),
    bullets: bullets.slice(0, MAX_BULLETS).map((b) => ({ text: b.text, tags: detectTechs(b.text).map((t) => t.id) })),
  };
}

function skillGroups(techs: Tech[], order: SkillsOrder): SkillGroup[] {
  const byCategory = new Map<TechCategory, string[]>();
  for (const tech of techs) byCategory.set(tech.category, [...(byCategory.get(tech.category) ?? []), tech.name]);
  return CATEGORY_ORDER[order]
    .filter((category) => byCategory.has(category))
    .map((category) => ({ label: category, content: (byCategory.get(category) ?? []).join(', ') }));
}

function parseEducation(lines: string[]): Profile['education'] {
  const years = lines.map((l) => PERIOD.exec(l)?.[0] ?? /\b(?:19|20)\d{2}\b/.exec(l)?.[0]).find(Boolean) ?? '';
  // Titulación y centro pueden venir en la misma línea separados por «|» o «·».
  const content = lines
    .flatMap((l) => l.replace(PERIOD, '').split(/\s*[|·]\s*/))
    .map((part) => part.trim())
    .filter(Boolean);
  return { degree: content[0] ?? '', school: content[1] ?? '', years };
}

function parseLanguages(lines: string[], full: string): Profile['languages'] {
  if (lines.length > 0) return { name: lines[0], detail: lines.slice(1).join('; ') };
  const english = /(ingl[eé]s|english)\s*[:\-–(]?\s*(A1|A2|B1|B2|C1|C2)/i.exec(full);
  return english ? { name: `Inglés ${english[2].toUpperCase()}`, detail: '' } : { name: '', detail: '' };
}

/**
 * Convierte el texto de un CV en un perfil aprovechable. Es una heurística: reconoce secciones habituales
 * (experiencia, formación, habilidades, idiomas) y las tecnologías del catálogo, y la persona revisa el
 * resultado antes de guardarlo. No inventa nada: lo que no encuentra queda vacío.
 */
export function parseCv(raw: string): Profile {
  const lines = cleanLines(raw);
  const sections = splitSections(lines);
  const full = lines.join('\n');
  const techs = detectTechs(full);
  const experienceSource = sections.experience.length > 0 ? sections.experience : sections.projects;

  return {
    ...parseHeader(sections.header.length > 0 ? sections.header : lines, full),
    ...parseExperience(experienceSource),
    skills: {
      backend_first: skillGroups(techs, 'backend_first'),
      fullstack: skillGroups(techs, 'fullstack'),
      frontend_first: skillGroups(techs, 'frontend_first'),
    },
    education: parseEducation(sections.education),
    languages: parseLanguages(sections.languages, full),
  };
}
