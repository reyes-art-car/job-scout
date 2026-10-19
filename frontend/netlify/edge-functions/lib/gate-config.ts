// Valor por defecto: sin hash el sitio falla cerrado (503). En Netlify lo sobrescribe `scripts/write-gate-config.mjs`
// durante el build con el SHA-256 de SITE_PASSWORD. No pongas aquí ninguna contraseña.
export const PASSWORD_HASH = '';
