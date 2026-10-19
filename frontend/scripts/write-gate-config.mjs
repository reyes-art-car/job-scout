// Se ejecuta en el build de Netlify: guarda el SHA-256 de SITE_PASSWORD para la Edge Function `gate`.
// Las Edge Functions no ven las variables definidas en el panel de Netlify, pero el build sí.
import { createHash } from 'node:crypto';
import { writeFileSync } from 'node:fs';

// SHA-256 solo es seguro para secretos de alta entropía (aquí, una contraseña aleatoria de ≥ 24 caracteres), no para
// contraseñas de personas; un hash lento (PBKDF2/scrypt) no cabe en el límite de CPU de 50 ms de las Edge Functions.
const MIN_LENGTH = 24;
const password = process.env.SITE_PASSWORD ?? '';
const strong = password.length >= MIN_LENGTH;
// Este fichero está excluido de CodeQL en .github/codeql/codeql-config.yml por el motivo anterior.
const hash = strong ? createHash('sha256').update(password, 'utf8').digest('hex') : '';
const target = new URL('../netlify/edge-functions/lib/gate-config.ts', import.meta.url);

writeFileSync(target, `// Generado en el build. No editar.\nexport const PASSWORD_HASH = '${hash}';\n`);
if (hash) console.log('gate: hash de SITE_PASSWORD escrito.');
else if (password) console.error(`gate: SITE_PASSWORD tiene menos de ${MIN_LENGTH} caracteres; el sitio responderá 503.`);
else console.error('gate: SITE_PASSWORD no está definida en el build; el sitio responderá 503.');
