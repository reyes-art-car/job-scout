// Ejecutar con: deno test --allow-env netlify/tests/gate.test.ts
import { assertEquals } from 'jsr:@std/assert@1';

let password: string | undefined = 'clave-de-prueba';
// deno-lint-ignore no-explicit-any
(globalThis as any).Netlify = { env: { get: () => password } };
const { default: gate, passwordFrom, samePassword } = await import('../edge-functions/gate.ts');

const basic = (user: string, pass: string) => `Basic ${btoa(`${user}:${pass}`)}`;
const next = { next: () => Promise.resolve(new Response('contenido')) };
const call = (auth?: string) =>
  // deno-lint-ignore no-explicit-any
  gate(new Request('https://x.test/', { headers: auth ? { authorization: auth } : {} }), next as any);

Deno.test('sin credenciales responde 401 con desafío Basic', async () => {
  const response = await call();
  assertEquals(response.status, 401);
  assertEquals(response.headers.get('www-authenticate')?.startsWith('Basic'), true);
});

Deno.test('contraseña incorrecta o cabecera mal formada: 401', async () => {
  for (const auth of [basic('a', 'mal'), 'Basic ???', 'Bearer clave-de-prueba', basic('a', '')]) {
    assertEquals((await call(auth)).status, 401);
  }
});

Deno.test('contraseña correcta sirve el contenido, con cualquier usuario y con ":" en la clave', async () => {
  assertEquals(await (await call(basic('cualquiera', 'clave-de-prueba'))).text(), 'contenido');
  password = 'a:b';
  assertEquals((await call(basic('u', 'a:b'))).status, 200);
  password = 'clave-de-prueba';
});

Deno.test('sin SITE_PASSWORD falla cerrado (503)', async () => {
  password = undefined;
  assertEquals((await call(basic('u', 'x'))).status, 503);
  password = 'clave-de-prueba';
});

Deno.test('utilidades', async () => {
  assertEquals(passwordFrom(null), null);
  assertEquals(passwordFrom(basic('u', 'p')), 'p');
  assertEquals(await samePassword('a', 'a'), true);
  assertEquals(await samePassword('a', 'b'), false);
});
