// Ejecutar con: deno test netlify/tests/gate.test.ts
import { assertEquals } from 'jsr:@std/assert@1';
import { createGate, matchesHash, passwordFrom, sha256Hex } from '../edge-functions/gate.ts';

const PASSWORD = 'clave-de-prueba';
const hash = await sha256Hex(PASSWORD);
const basic = (user: string, pass: string) => `Basic ${btoa(`${user}:${pass}`)}`;
const next = { next: () => Promise.resolve(new Response('contenido')) };
const call = (gate: ReturnType<typeof createGate>, auth?: string) =>
  gate(new Request('https://x.test/', { headers: auth ? { authorization: auth } : {} }), next);

Deno.test('sin credenciales responde 401 con desafío Basic', async () => {
  const response = await call(createGate(hash));
  assertEquals(response.status, 401);
  assertEquals(response.headers.get('www-authenticate')?.startsWith('Basic'), true);
});

Deno.test('contraseña incorrecta o cabecera mal formada: 401', async () => {
  const gate = createGate(hash);
  for (const auth of [basic('a', 'mal'), 'Basic ???', `Bearer ${PASSWORD}`, basic('a', '')]) {
    assertEquals((await call(gate, auth)).status, 401);
  }
});

Deno.test('contraseña correcta sirve el contenido, con cualquier usuario, ":" y acentos', async () => {
  assertEquals(await (await call(createGate(hash), basic('cualquiera', PASSWORD))).text(), 'contenido');
  const special = 'a:ñ€';
  const bytes = new TextEncoder().encode(`u:${special}`);
  const header = `Basic ${btoa(String.fromCharCode(...bytes))}`;
  assertEquals((await call(createGate(await sha256Hex(special)), header)).status, 200);
});

Deno.test('sin hash válido falla cerrado (503), incluso con credenciales', async () => {
  for (const bad of ['', 'no-es-un-hash']) {
    assertEquals((await call(createGate(bad), basic('u', PASSWORD))).status, 503);
  }
});

Deno.test('utilidades', async () => {
  assertEquals(passwordFrom(null), null);
  assertEquals(passwordFrom(basic('u', 'p')), 'p');
  assertEquals(await matchesHash('a', await sha256Hex('a')), true);
  assertEquals(await matchesHash('a', await sha256Hex('b')), false);
  assertEquals(
    await sha256Hex('abc'),
    'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad',
  );
});
