/** Extrae texto de un CV subido (PDF, DOCX o TXT). Todo ocurre en el navegador: el archivo no se envía a ningún servidor. */

export const MAX_CV_BYTES = 5 * 1024 * 1024;
const MAX_PDF_PAGES = 15;
const MAX_XML_BYTES = 20 * 1024 * 1024;
const MAX_TEXT_CHARS = 200_000;

export type CvFormat = 'pdf' | 'docx' | 'txt';

export class CvFileError extends Error {}

const ascii = (bytes: Uint8Array, length: number): string => String.fromCharCode(...bytes.slice(0, length));

/** Decide el formato por el contenido y no solo por la extensión, para rechazar archivos renombrados. */
export function detectFormat(name: string, head: Uint8Array): CvFormat {
  const extension = name.toLowerCase().split('.').pop() ?? '';
  if (ascii(head, 5) === '%PDF-') return 'pdf';
  if (head[0] === 0x50 && head[1] === 0x4b) {
    if (extension === 'docx') return 'docx';
    throw new CvFileError('Solo se admiten documentos de Word en formato .docx (no .doc).');
  }
  if (extension === 'txt' && !head.slice(0, 1024).includes(0)) return 'txt';
  throw new CvFileError('Formato no admitido. Sube tu CV en PDF, DOCX o TXT.');
}

const ENTITIES: Record<string, string> = { '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', '&apos;': "'" };

/** Convierte el XML de un documento Word en líneas de texto, marcando los párrafos de lista como viñetas. */
export function docxXmlToText(xml: string): string {
  return xml
    .split(/<w:p[ >]/)
    .slice(1)
    .map((paragraph) => {
      const text = paragraph
        .replace(/<w:tab\/>/g, ' ')
        .replace(/<w:br\/>/g, '\n')
        .replace(/<[^>]+>/g, '')
        .replace(/&(?:amp|lt|gt|quot|apos);/g, (entity) => ENTITIES[entity]);
      return /<w:numPr>/.test(paragraph) && text.trim() ? `• ${text}` : text;
    })
    .join('\n');
}

async function pdfText(data: Uint8Array): Promise<string> {
  const pdfjs = await import('pdfjs-dist');
  pdfjs.GlobalWorkerOptions.workerSrc = 'pdf/pdf.worker.min.mjs';
  const task = pdfjs.getDocument({ data, enableXfa: false });
  try {
    const document = await task.promise;
    const parts: string[] = [];
    for (let number = 1; number <= Math.min(document.numPages, MAX_PDF_PAGES); number++) {
      const content = await (await document.getPage(number)).getTextContent();
      parts.push(...content.items.map((item) => ('str' in item ? item.str + (item.hasEOL ? '\n' : ' ') : '')));
      parts.push('\n');
    }
    return parts.join('');
  } finally {
    await task.destroy();
  }
}

async function docxText(data: Uint8Array): Promise<string> {
  const { unzipSync, strFromU8 } = await import('fflate');
  // Se descomprime solo el documento principal y con tope de tamaño, para no abrir un «zip bomb».
  const files = unzipSync(data, { filter: (file) => file.name === 'word/document.xml' && file.originalSize <= MAX_XML_BYTES });
  const xml = files['word/document.xml'];
  if (!xml) throw new CvFileError('No se ha podido leer el documento de Word.');
  return docxXmlToText(strFromU8(xml));
}

export async function extractCvText(file: File): Promise<string> {
  if (file.size === 0) throw new CvFileError('El archivo está vacío.');
  if (file.size > MAX_CV_BYTES) throw new CvFileError('El archivo supera los 5 MB.');
  const data = new Uint8Array(await file.arrayBuffer());
  const format = detectFormat(file.name, data);
  let text: string;
  try {
    text = format === 'pdf' ? await pdfText(data) : format === 'docx' ? await docxText(data) : new TextDecoder('utf-8').decode(data);
  } catch (error) {
    if (error instanceof CvFileError) throw error;
    throw new CvFileError('No se ha podido leer el archivo. Comprueba que no esté protegido con contraseña ni dañado.');
  }
  text = text.slice(0, MAX_TEXT_CHARS);
  if (text.replace(/\s/g, '').length < 40) {
    throw new CvFileError('No se ha encontrado texto en el archivo. Si es un PDF escaneado (una imagen), expórtalo de nuevo con texto seleccionable.');
  }
  return text;
}
