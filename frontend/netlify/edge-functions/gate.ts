/**
 * Puerta de acceso del sitio en Netlify: pide contraseña (HTTP Basic) antes de servir CUALQUIER fichero,
 * incluido el código de la aplicación. La contraseña vive en la variable de entorno SITE_PASSWORD.
 * Falla cerrado: sin SITE_PASSWORD el sitio responde 503 en lugar de quedar abierto.
 */

// Tipos mínimos del entorno de Edge Functions de Netlify (evita depender de un paquete solo para tipos).
interface Context {
  next(): Promise<Response>;
}
declare const Netlify: { env: { get(name: string): string | undefined; toObject?(): Record<string, string> } };

const encoder = new TextEncoder();

async function digest(value: string): Promise<Uint8Array> {
  return new Uint8Array(await crypto.subtle.digest('SHA-256', encoder.encode(value)));
}

/** Comparación en tiempo constante (sobre hashes de igual longitud) para no filtrar la clave por latencia. */
export async function samePassword(supplied: string, expected: string): Promise<boolean> {
  const [a, b] = await Promise.all([digest(supplied), digest(expected)]);
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a[i] ^ b[i];
  return diff === 0;
}

/** Extrae la contraseña de `Authorization: Basic base64(usuario:contraseña)`; el usuario es indiferente. */
export function passwordFrom(header: string | null): string | null {
  if (!header?.startsWith('Basic ')) return null;
  try {
    const decoded = atob(header.slice(6).trim());
    const separator = decoded.indexOf(':');
    return separator < 0 ? null : decoded.slice(separator + 1);
  } catch {
    return null;
  }
}

const HEADERS = { 'Cache-Control': 'no-store', 'X-Robots-Tag': 'noindex, nofollow' };

export default async function gate(request: Request, context: Context): Promise<Response> {
  const expected = Netlify.env.get('SITE_PASSWORD');
  if (!expected) {
    // Solo nombres de variables (nunca valores) para diagnosticar una configuración incompleta.
    console.error('SITE_PASSWORD no definida. Variables visibles:', Object.keys(Netlify.env.toObject?.() ?? {}).join(', '));
    return new Response('Sitio no configurado.', { status: 503, headers: HEADERS });
  }
  const supplied = passwordFrom(request.headers.get('authorization'));
  if (supplied !== null && (await samePassword(supplied, expected))) {
    const response = await context.next();
    for (const [name, value] of Object.entries(HEADERS)) response.headers.set(name, value);
    return response;
  }
  return new Response('Acceso privado.', {
    status: 401,
    headers: { ...HEADERS, 'WWW-Authenticate': 'Basic realm="Acceso privado", charset="UTF-8"' },
  });
}

export const config = { path: '/*' };
