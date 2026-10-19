// Se ejecuta en el build de Netlify: guarda el SHA-256 de SITE_PASSWORD para la Edge Function `gate`.
// Las Edge Functions no ven las variables definidas en el panel de Netlify, pero el build sí.
import { createHash } from 'node:crypto';
import { writeFileSync } from 'node:fs';

const password = process.env.SITE_PASSWORD ?? '';
const hash = password ? createHash('sha256').update(password, 'utf8').digest('hex') : '';
const target = new URL('../netlify/edge-functions/lib/gate-config.ts', import.meta.url);

writeFileSync(target, `// Generado en el build. No editar.\nexport const PASSWORD_HASH = '${hash}';\n`);
console.log(
  hash
    ? 'gate: hash de SITE_PASSWORD escrito.'
    : 'gate: SITE_PASSWORD no está definida en el build; el sitio responderá 503.',
);
