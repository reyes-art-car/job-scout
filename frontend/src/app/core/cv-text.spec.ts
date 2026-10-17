import { CvFileError, MAX_CV_BYTES, detectFormat, docxXmlToText, extractCvText } from './cv-text';

const bytes = (text: string) => new TextEncoder().encode(text);

describe('detectFormat', () => {
  it('reconoce un PDF por su contenido aunque cambie la extensión', () => {
    expect(detectFormat('cv.txt', bytes('%PDF-1.7'))).toBe('pdf');
  });

  it('acepta DOCX y TXT', () => {
    expect(detectFormat('cv.docx', new Uint8Array([0x50, 0x4b, 3, 4]))).toBe('docx');
    expect(detectFormat('cv.txt', bytes('hola'))).toBe('txt');
  });

  it('rechaza otros formatos y binarios renombrados', () => {
    expect(() => detectFormat('cv.exe', new Uint8Array([0x4d, 0x5a]))).toThrowError(CvFileError);
    expect(() => detectFormat('cv.txt', new Uint8Array([0, 1, 2, 3]))).toThrowError(CvFileError);
    expect(() => detectFormat('cv.zip', new Uint8Array([0x50, 0x4b, 3, 4]))).toThrowError(CvFileError);
  });
});

describe('docxXmlToText', () => {
  it('separa párrafos, decodifica entidades y marca las listas con viñeta', () => {
    const xml =
      '<w:p><w:r><w:t>Ada &amp; Co</w:t></w:r></w:p>' +
      '<w:p><w:pPr><w:numPr><w:ilvl w:val="0"/></w:numPr></w:pPr><w:r><w:t>Logro uno</w:t></w:r></w:p>';
    expect(docxXmlToText(xml)).toBe('Ada & Co\n• Logro uno');
  });
});

describe('extractCvText', () => {
  it('lee un TXT', async () => {
    const text = 'Ada Lovelace\nDesarrolladora con experiencia en Java y Angular en proyectos reales.';
    expect(await extractCvText(new File([text], 'cv.txt', { type: 'text/plain' }))).toBe(text);
  });

  it('rechaza archivos vacíos, demasiado grandes o sin texto', async () => {
    await expectAsync(extractCvText(new File([], 'cv.txt'))).toBeRejectedWithError(CvFileError);
    await expectAsync(extractCvText(new File([new Uint8Array(MAX_CV_BYTES + 1)], 'cv.txt'))).toBeRejectedWithError(CvFileError);
    await expectAsync(extractCvText(new File(['poco'], 'cv.txt'))).toBeRejectedWithError(CvFileError);
  });

  it('rechaza un PDF dañado con un mensaje claro', async () => {
    await expectAsync(extractCvText(new File(['%PDF-1.7 esto no es un pdf de verdad'], 'cv.pdf'))).toBeRejectedWithError(CvFileError);
  });
});
