import { Offer, Profile } from './models';
import { TailoredCv } from './tailoring';

const CSV_COLUMNS: { header: string; value: (o: Offer) => string | number | null }[] = [
  { header: 'ID', value: (o) => o.code },
  { header: 'Prioridad', value: (o) => o.priority },
  { header: '% Compatibilidad', value: (o) => `${o.compatibility}%` },
  { header: 'Puesto', value: (o) => o.title },
  { header: 'Empresa', value: (o) => o.company },
  { header: 'Portal', value: (o) => o.portal },
  { header: 'Enlace', value: (o) => o.url },
  { header: 'Fecha publicación', value: (o) => o.published_date },
  { header: 'Ubicación', value: (o) => o.location },
  { header: 'Modalidad', value: (o) => o.modality },
  { header: 'Tipo contrato', value: (o) => o.contract_type },
  { header: 'Salario', value: (o) => o.salary },
  { header: 'Experiencia solicitada', value: (o) => o.experience_required },
  { header: 'Tecnologías obligatorias', value: (o) => o.mandatory_tech },
  { header: 'Tecnologías deseables', value: (o) => o.desirable_tech },
  { header: 'Requisitos que cumplo', value: (o) => o.requirements_met },
  { header: 'Requisitos que NO cumplo', value: (o) => o.requirements_missing },
  { header: 'Motivo puntuación', value: (o) => o.score_reason },
  { header: 'Estado candidatura', value: (o) => o.kanban_status },
  { header: 'Observaciones', value: (o) => o.notes },
];

function csvCell(value: string | number | null): string {
  const text = value === null || value === undefined ? '' : String(value);
  // Evita la inyección de fórmulas al abrir el CSV en Excel.
  const safe = /^[=+\-@\t\r]/.test(text) ? `'${text}` : text;
  return `"${safe.replace(/"/g, '""')}"`;
}

/** CSV con «;» y BOM UTF-8: Excel en español lo abre con las columnas y los acentos correctos. */
export function offersToCsv(offers: readonly Offer[]): string {
  const rows = [
    CSV_COLUMNS.map((c) => csvCell(c.header)).join(';'),
    ...offers.map((o) => CSV_COLUMNS.map((c) => csvCell(c.value(o))).join(';')),
  ];
  return '﻿' + rows.join('\r\n');
}

export function downloadFile(filename: string, content: string, mime: string): void {
  const url = URL.createObjectURL(new Blob([content], { type: `${mime};charset=utf-8` }));
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function slug(text: string): string {
  return text
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-zA-Z0-9]+/g, '')
    .slice(0, 40);
}

const esc = (s: string) =>
  s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

const WORD_WRAPPER = (title: string, body: string) =>
  `<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word"><head><meta charset="utf-8"><title>${esc(title)}</title><style>body{font-family:Calibri,Arial,sans-serif;font-size:10pt;color:#222}h1{font-size:18pt;margin:0;color:#1a6870}h2{font-size:10pt;color:#1a6870;border-bottom:1px solid #1a6870;margin:12pt 0 4pt}p{margin:3pt 0}li{margin:2pt 0}.sub{font-size:10pt}.ct{font-size:9pt;color:#444}</style></head><body>${body}</body></html>`;

/** HTML que Word abre y guarda como .docx sin dependencias adicionales. */
export function cvToWordHtml(profile: Profile, cv: TailoredCv): string {
  const skills = cv.groups
    .map(
      (g) =>
        `<p><b>${esc(g.label)}:</b> ${g.items.map((i) => esc(i.text)).join(', ')}</p>`,
    )
    .join('');
  const bullets = cv.bullets.map((b) => `<li>${esc(b.text)}</li>`).join('');
  return WORD_WRAPPER(
    `CV ${profile.name}`,
    `<h1>${esc(profile.name.toUpperCase())}</h1>
<p class="sub">${esc(cv.title)}</p>
<p class="ct">${esc(profile.location)} | ${esc(profile.email)} | ${esc(profile.linkedin)}</p>
<h2>PERFIL PROFESIONAL</h2><p>${esc(cv.summary)}</p>
<h2>EXPERIENCIA Y PROYECTOS</h2>
<p><b>${esc(profile.company.toUpperCase())} | ${esc(profile.role)}</b> — ${esc(profile.period)}</p>
<p><i>${esc(profile.project)}</i></p><ul>${bullets}</ul>
<h2>COMPETENCIAS TÉCNICAS</h2>${skills}
<h2>FORMACIÓN</h2><p><b>${esc(profile.education.degree)}</b> | ${esc(profile.education.school)} | ${esc(profile.education.years)}</p>
<h2>IDIOMAS</h2><p><b>${esc(profile.languages.name)}</b> — ${esc(profile.languages.detail)}</p>`,
  );
}

export function letterToWordHtml(profile: Profile, text: string): string {
  const paragraphs = text
    .split('\n')
    .map((l) => (l.trim() === '' ? '<p>&nbsp;</p>' : `<p>${esc(l)}</p>`))
    .join('');
  return WORD_WRAPPER(
    `Carta ${profile.name}`,
    `<h1 style="font-size:16pt">${esc(profile.name)}</h1><p class="ct">${esc(profile.location)} | ${esc(profile.email)}</p><p>&nbsp;</p>${paragraphs}`,
  );
}
