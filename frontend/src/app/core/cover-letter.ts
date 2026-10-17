import { Offer, Profile } from './models';
import { analyzeOffer, joinEs, topMatched } from './tailoring';

export type Tone = 'formal' | 'cercano';

export interface LetterOptions {
  tone: Tone;
  /** Añade un párrafo honesto sobre las tecnologías de la oferta que aún no acredita. */
  mentionGaps: boolean;
  availability: string;
  /** Texto adicional de la oferta (por ejemplo, pegado desde LinkedIn). */
  description?: string;
}

export interface Letter {
  subject: string;
  greeting: string;
  paragraphs: string[];
  closing: string;
  signature: string;
}

type LetterOffer = Pick<
  Offer,
  'title' | 'company' | 'portal' | 'modality' | 'mandatory_tech' | 'desirable_tech'
>;

export const DEFAULT_LETTER_OPTIONS: LetterOptions = {
  tone: 'formal',
  mentionGaps: false,
  availability: 'de inmediato',
};

const lowerFirst = (text: string): string => text.charAt(0).toLowerCase() + text.slice(1);

export function buildCoverLetter(
  profile: Profile,
  offer: LetterOffer,
  opts: LetterOptions = DEFAULT_LETTER_OPTIONS,
): Letter {
  const analysis = analyzeOffer(offer, opts.description ?? '');
  const key = topMatched(analysis, 2);
  const remote = /remot/i.test(offer.modality) && !/h[ií]brid/i.test(offer.modality);
  const title = offer.title.trim();
  const company = offer.company.trim();

  const intro =
    opts.tone === 'formal'
      ? `Me dirijo a ustedes para presentar mi candidatura al puesto de ${title} en ${company}, publicado en ${offer.portal}. Actualmente trabajo como ${lowerFirst(profile.role)} en ${profile.company}, donde mi práctica diaria con ${joinEs(key)} encaja de forma directa con los requisitos técnicos de la oferta.`
      : `Les escribo porque el puesto de ${title} en ${company} encaja muy bien con lo que hago cada día: soy ${lowerFirst(profile.role)} en ${profile.company} y trabajo a diario con ${joinEs(key)}.`;

  const evidence =
    'En el currículo adjunto encontrará el detalle: soy la única desarrolladora de un CRM comercial en producción, con backend en Java y Spring Boot, persistencia mediante Spring Data JPA sobre PostgreSQL y MySQL, y seguridad resuelta con JWT, refresh tokens y control de roles (RBAC) sobre Spring Security. El despliegue lo automaticé con Docker y GitHub Actions sobre un VPS real.';

  const stack =
    analysis.role === 'backend'
      ? 'También cuido la calidad del código: pruebas con JUnit y Mockito, documentación de la API con OpenAPI/Swagger y una arquitectura por capas con principios SOLID, lo que facilita mantener y evolucionar el sistema.'
      : 'En el frontend construí también, de forma individual, la interfaz completa del CRM con Angular, TypeScript, Bootstrap, HTML5 y CSS3, con diseño responsive e integrada con la API REST del backend. Esta experiencia end-to-end, diseñando y conectando ambos extremos de la aplicación, es justo la perspectiva full stack que busca esta posición.';

  const cover = analysis.matched
    .filter((r) => !['english', 'excel-csv'].includes(r.tech.id))
    .slice(0, 6)
    .map((r) => r.tech.name);
  const matchPara =
    cover.length >= 3 ? `De los requisitos que menciona la oferta, cubro directamente ${joinEs(cover)}.` : null;

  const gaps = analysis.missing
    .filter((r) => r.origin === 'obligatoria' || r.tech.priority === 'A')
    .slice(0, 2)
    .map((r) => r.tech.name);
  const gapPara =
    opts.mentionGaps && gaps.length > 0
      ? `Soy consciente de que la oferta también valora ${joinEs(gaps)}. Todavía no lo he utilizado en producción y es un área en la que estoy profundizando activamente.`
      : null;

  const closing = remote
    ? `Puedo incorporarme ${opts.availability}, en modalidad 100% remota y a jornada completa. Quedo a su disposición para una entrevista y para resolver cualquier duda sobre mi candidatura.`
    : `Puedo incorporarme ${opts.availability} y a jornada completa. Quedo a su disposición para una entrevista y para resolver cualquier duda sobre mi candidatura.`;

  return {
    subject: `Candidatura al puesto de ${title} (ref. ${offer.portal})`,
    greeting: opts.tone === 'formal' ? 'Estimado/a responsable de selección:' : 'Hola, equipo de selección de ' + company + ':',
    paragraphs: [intro, evidence, stack, matchPara, gapPara].filter((p): p is string => p !== null),
    closing,
    signature: profile.name,
  };
}

export function letterToText(letter: Letter, company: string, dateLine: string): string {
  return [
    company,
    'Departamento de Selección',
    '',
    dateLine,
    '',
    `Asunto: ${letter.subject}`,
    '',
    letter.greeting,
    '',
    ...letter.paragraphs.flatMap((p) => [p, '']),
    letter.closing,
    '',
    'Atentamente,',
    letter.signature,
  ].join('\n');
}
