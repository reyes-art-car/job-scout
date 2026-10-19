/**
 * Puerta de acceso del sitio en Netlify: pide contraseña (HTTP Basic) antes de servir CUALQUIER fichero,
 * incluido el código de la aplicación. El hash SHA-256 de la contraseña lo escribe el build a partir de la
 * variable SITE_PASSWORD (ver scripts/write-gate-config.mjs). Falla cerrado: sin hash el sitio responde 503.
 */
import { PASSWORD_HASH } from './lib/gate-config.ts';

// Tipo mínimo del contexto de Edge Functions (evita depender de un paquete solo para tipos).
interface Context {
  next(): Promise<Response>;
}

const encoder = new TextEncoder();
const HASH_FORMAT = /^[0-9a-f]{64}$/;

export async function sha256Hex(value: string): Promise<string> {
  const digest = new Uint8Array(await crypto.subtle.digest('SHA-256', encoder.encode(value)));
  return Array.from(digest, (byte) => byte.toString(16).padStart(2, '0')).join('');
}

/** Compara la contraseña con el hash esperado en tiempo constante (ambos hex de 64 caracteres). */
export async function matchesHash(supplied: string, expectedHash: string): Promise<boolean> {
  if (!HASH_FORMAT.test(expectedHash)) return false;
  const actual = await sha256Hex(supplied);
  let diff = 0;
  for (let i = 0; i < actual.length; i++) diff |= actual.charCodeAt(i) ^ expectedHash.charCodeAt(i);
  return diff === 0;
}

/** Extrae la contraseña de `Authorization: Basic base64(usuario:contraseña)`; el usuario es indiferente. */
export function passwordFrom(header: string | null): string | null {
  if (!header?.startsWith('Basic ')) return null;
  try {
    const bytes = Uint8Array.from(atob(header.slice(6).trim()), (char) => char.charCodeAt(0));
    const decoded = new TextDecoder().decode(bytes);
    const separator = decoded.indexOf(':');
    return separator < 0 ? null : decoded.slice(separator + 1);
  } catch {
    return null;
  }
}

const HEADERS = { 'Cache-Control': 'no-store', 'X-Robots-Tag': 'noindex, nofollow' };

export function createGate(expectedHash: string) {
  return async function gate(request: Request, context: Context): Promise<Response> {
    if (!HASH_FORMAT.test(expectedHash)) {
      console.error('[gate] Sin hash de contraseña: SITE_PASSWORD no estaba definida durante el build.');
      return new Response('Sitio no configurado.', { status: 503, headers: HEADERS });
    }
    const supplied = passwordFrom(request.headers.get('authorization'));
    if (supplied !== null && (await matchesHash(supplied, expectedHash))) {
      const response = await context.next();
      for (const [name, value] of Object.entries(HEADERS)) response.headers.set(name, value);
      return response;
    }
    return new Response('Acceso privado.', {
      status: 401,
      headers: { ...HEADERS, 'WWW-Authenticate': 'Basic realm="Acceso privado", charset="UTF-8"' },
    });
  };
}

export default createGate(PASSWORD_HASH);

export const config = { path: '/*' };
