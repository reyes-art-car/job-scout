# Seguridad

Este documento recoge qué se protege, cómo, dónde está en el código y qué queda sin cubrir. La política para
informar de una vulnerabilidad está en [SECURITY.md](../SECURITY.md).

## Qué hay que proteger

Job Hopping & Learning maneja datos personales de una candidatura (currículums, cartas, teléfono, correo, la evaluación de cada
oferta) y ejecuta contenido que **no controla**: anuncios de empleo leídos de internet, salida de un modelo de
lenguaje y ficheros Excel importados.

| Superficie | Quién puede atacar | Qué se busca |
|---|---|---|
| API (`/api/*`) | Cualquiera que alcance el puerto | Leer o modificar ofertas, agotar el servicio, inyectar datos |
| Frontend | Un anuncio o un fichero con contenido hostil | XSS, robo del token, enlaces `javascript:` |
| Buscador diario (`automation/`) | Un anuncio con instrucciones ocultas («prompt injection») | Escribir ficheros fuera de la carpeta, fórmulas en el Excel |
| Importación de Excel | Un Excel manipulado | Memoria, inyección de fórmulas, enlaces peligrosos |
| Repositorio público | Cualquiera en GitHub | Filtración de datos personales o secretos |

## Controles implementados

### API (FastAPI)

| Amenaza | Control | Código | Prueba |
|---|---|---|---|
| Acceso sin autorización | Token Bearer, **denegado por defecto**: solo `/api/health` es público. Comparación de tiempo constante (`hmac.compare_digest`) | `api/security/auth.py` | `test_every_non_public_route_is_protected` recorre las rutas y falla si alguna nueva no exige token |
| Configuración insegura en producción | La app **no arranca** sin `API_TOKEN` de 32+ caracteres ni con CORS `*` | `config.py` | `test_production_requires_a_strong_token` |
| Token vacío = acceso abierto | Un `API_TOKEN=` vacío se interpreta como «sin token», nunca como token vacío válido | `config.py` | `test_blank_token_is_treated_as_no_token` |
| Fuerza bruta y abuso | Límite por IP y minuto (lectura 120 · escritura 30 · exportación 6), ventana deslizante con memoria acotada, `429` con `Retry-After` | `api/security/rate_limit.py` | `test_rate_limit_*`, `test_limiter_*` |
| Suplantación de IP | `X-Forwarded-For` solo se usa con `TRUST_PROXY=true` y se toma el **último** valor (el que añade nuestro proxy) | `rate_limit.client_ip` | `test_client_ip_ignores_forwarded_header…` |
| Cuerpos enormes | Máximo 1 MB por `Content-Length` y también en transferencias por fragmentos | `api/security/body_limit.py` | `test_oversized_body_is_rejected` |
| Paginación y filtros sin tope | `page_size ≤ 500`, `search ≤ 100`, rangos de compatibilidad | `api/routers/offers.py` | `test_pagination_is_bounded` |
| XSS almacenado | HTML y caracteres de control (incluidos los de dirección bidi) se eliminan al **entrar** con `nh3`; longitud máxima por campo | `shared/sanitize.py`, `api/schemas/types.py` | `test_html_is_stripped…`, `test_clean_text` |
| Enlaces peligrosos | Solo `http`/`https` absolutos: se rechazan `javascript:`, `data:`, `file:`, `//host` | `shared/sanitize.validate_http_url` | `test_non_http_urls_are_rejected` |
| *Mass assignment* | Esquemas con `extra="forbid"`: un campo desconocido (`id`, `code`, `adapted_cv_filename`…) es un 422, no se ignora | `api/schemas/offer_schemas.py` | `test_unknown_fields_are_rejected…` |
| Inyección SQL | Solo SQLAlchemy con parámetros; los comodines `%` y `_` de la búsqueda se escapan | `sqlalchemy_offer_repository._contains` | `test_sql_injection_attempts_are_inert`, `test_search_wildcards…` |
| *Path traversal* al descargar un CV | El nombre se reduce a su `name`, se resuelve la ruta real (también enlaces simbólicos) y debe seguir dentro de la carpeta de CVs | `infrastructure/files/cv_locator.py` | `test_locator_*`, `test_cv_download_is_confined…` |
| Fugas por errores | Errores genéricos con identificador de incidente; el detalle va solo al log. Los 422 no devuelven el valor enviado | `api/error_handlers.py` | `test_unexpected_errors_do_not_leak…`, `test_validation_errors_do_not_echo…` |
| Cabeceras | `X-Content-Type-Options`, `X-Frame-Options: DENY`, CSP `default-src 'none'`, `Referrer-Policy`, `Permissions-Policy`, `Cache-Control: no-store`, HSTS en producción; también en los 500 | `api/security/headers.py` | `test_security_headers_are_present` |
| Exposición de la API | `/docs` y `/openapi.json` desactivados en producción; `TrustedHostMiddleware` | `main.py` | `test_docs_are_hidden_in_production`, `test_unknown_host_header…` |
| CORS permisivo | Orígenes explícitos, sin credenciales, solo `GET/POST/PATCH` y cabeceras necesarias | `main.py` | `test_cors_only_allows_configured_origins` |
| Secretos en logs o `repr` | `SecretStr` para el token y la clave de Anthropic | `config.py` | `test_secrets_are_not_printed` |

### Frontend (Angular)

| Amenaza | Control | Código |
|---|---|---|
| XSS | Plantillas de Angular (escapan por defecto). **ESLint prohíbe** `innerHTML`, `outerHTML`, `document.write`, `eval` y `bypassSecurityTrust*` | `eslint.config.js` |
| Inyección de scripts | CSP en `index.html` (`script-src 'self'`, `object-src 'none'`, `base-uri 'self'`…) y sin scripts inline en producción (`inlineCritical: false`). Comprobado cargando la app compilada en Chrome sin violaciones | `src/index.html`, `angular.json` |
| Datos manipulados (red o `localStorage`) | Toda oferta se valida y normaliza (tipos, rangos, longitudes, estado válido, URL http/https) antes de usarla; lo que no encaja se descarta | `core/offer-validation.ts` |
| Robo del token | Se guarda en `sessionStorage` (se borra al cerrar la pestaña), nunca en `localStorage`, y **solo se envía a `/api/`**, jamás a dominios de terceros | `core/auth.ts` |
| Enlaces salientes | `rel="noopener noreferrer"` y URL validada | `offers.html` |
| CSV con fórmulas | Las celdas que empiezan por `=`, `+`, `-` o `@` se neutralizan (también en el backend) | `core/export.ts`, `export_offers.py` |
| Salida a Word | Todo el contenido se escapa antes de generar el HTML | `core/export.ts` |

### Buscador diario (`automation/`)

La respuesta del modelo se trata como **entrada no confiable** (un anuncio puede incluir instrucciones ocultas).

| Amenaza | Control | Código |
|---|---|---|
| El modelo (o un anuncio) elige el nombre del CV: `../../x.docx`, rutas absolutas, `.exe` | Solo `[A-Za-z0-9_.-]` terminado en `.docx`; si no, se genera uno limpio. Doble comprobación al escribir: la carpeta de destino debe ser exactamente la de CVs | `jobsearch/offer.py`, `cv_docx.py` |
| Fórmulas en el Excel (`=HYPERLINK(...)`) | Todas las celdas se escriben como **texto** | `jobsearch/excel_store.py` |
| URLs `javascript:` / `data:` | Se descartan; el hipervínculo solo apunta a URLs ya validadas | `jobsearch/offer.py` |
| Campos que el modelo no debe decidir | El estado de la candidatura y el ID los fija la aplicación, no el modelo | `jobsearch/offer.py` |
| El modelo ejecuta acciones | Claude Code se lanza solo con `WebSearch,WebFetch` (sin Bash ni escritura) y el prompt va por stdin, sin shell | `jobsearch/llm.py` |
| Instrucciones dentro del anuncio | El prompt indica que el contenido es no confiable y que se ignoren órdenes incluidas en él | `prompts/search_prompt.txt` |
| Respuestas gigantes o malformadas | Límite de tamaño y de número de ofertas; el JSON se extrae con `raw_decode`, sin expresiones regulares frágiles | `jobsearch/parsing.py` |

### Datos y repositorio

- `.gitignore` excluye CVs, cartas, Excel de ofertas, logs, bases de datos, el perfil con datos de contacto y `.env`.
- `backend/config/candidate_profile.example.yaml` es una plantilla sin datos reales.
- Hook `pre-commit` (`.githooks/`) que bloquea ficheros privados y patrones de claves; **gitleaks** en CI.
- Importación de Excel: máximo 5.000 filas, texto saneado y recortado, solo URLs http/https.

### Despliegue (`backend/Dockerfile`, `infra/`)

- Imagen multi-etapa, usuario sin privilegios ni shell, sin caché de pip, `HEALTHCHECK`.
- `docker-compose`: sistema de ficheros de solo lectura, `cap_drop: ALL`, `no-new-privileges`, límites de memoria y procesos, la API **no se publica** en el host (solo nginx llega a ella).
- nginx: `server_tokens off`, límites de ritmo y de conexiones por IP, tiempos de cabecera/cuerpo cortos (slowloris), CSP con `frame-ancestors`, la IP real se **sustituye** en `X-Forwarded-For`.

## Puesta en producción

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"   # → API_TOKEN
```

```ini
APP_ENV=production
API_TOKEN=<token generado>
CORS_ORIGINS=https://tu-dominio
ALLOWED_HOSTS=tu-dominio
TRUST_PROXY=true        # solo si hay nginx delante
```

Con `APP_ENV=production` la aplicación se niega a arrancar si falta el token o CORS es `*`. Termina TLS en un proxy
(Caddy, Traefik, Cloudflare…) y deja que añada `Strict-Transport-Security`.

## Dependencias

- `pip-audit` sobre `backend/requirements.txt` y `automation/requirements.txt`: **sin vulnerabilidades conocidas**.
  Al empezar esta revisión había 32 avisos en `starlette`, `python-multipart`, `pytest` y `pdfminer-six`; se actualizaron
  y se eliminaron las dependencias que el código no usaba.
- `npm audit --omit=dev` (lo que llega al navegador): **0 vulnerabilidades**.
- Dependabot semanal (pip, npm, Docker, GitHub Actions) y revisión programada cada lunes en CI.
- Versiones **fijadas** (`==`) en el backend para builds reproducibles.

## Riesgo residual y limitaciones

Lo siguiente **no** está resuelto, y conviene saberlo antes de exponer la aplicación:

1. **Un solo token estático, sin roles ni usuarios.** Es adecuado para una aplicación personal; si hubiera varios
   usuarios habría que pasar a JWT con *refresh tokens* y RBAC.
2. **El limitador de ritmo es en memoria**: vale para una instancia. Con varias réplicas debe moverse a Redis o dejarse
   solo en nginx.
3. **El token vive en `sessionStorage`**: un XSS lo leería. La CSP y el escapado de Angular lo mitigan, pero la opción
   más fuerte sería una cookie `HttpOnly` con `SameSite=Strict` (habría que añadir protección CSRF).
4. **La CSP admite `style-src 'unsafe-inline'`** porque Angular inyecta estilos de componente. Se podría eliminar con
   un *nonce* servido por el servidor (`ngCspNonce`).
5. **Aviso `braces` (ReDoS, severidad alta) en herramientas de desarrollo** (Karma, ESLint, Angular CLI). No existe
   versión corregida en la rama 3.x y solo afecta al expandir patrones de ficheros definidos por el desarrollador.
   No llega a producción. Se vigila en cada revisión.
6. **SQLite sin cifrar en disco.** Cifra el volumen del servidor o usa PostgreSQL con cifrado en reposo.
7. **Sin registro de auditoría** de quién cambió qué. Hoy los errores se registran con un identificador y las
   peticiones no.
8. **El buscador usa tu sesión de Claude Code.** Quien tenga acceso a tu equipo tiene acceso a ella; está fuera del
   alcance de este repositorio.
9. **Imágenes Docker sin probar en esta revisión**: el demonio de Docker no estaba disponible. Los ficheros siguen
   las prácticas habituales, pero ejecuta `docker compose up --build` y comprueba `/api/health` antes de fiarte.

## Protección del proyecto contra copias

- **Licencia propietaria** (`LICENSE`): todos los derechos reservados. Es lo que da base legal para reclamar una copia.
  La licencia MIT anterior ya se concedió a quien clonó el repositorio antes del cambio y no se puede retirar.
- **Clave de acceso** (`API_TOKEN`, ≥ 32 caracteres en producción): sin ella la API devuelve 401 y la aplicación
  muestra la pantalla `/acceso`. Es una clave compartida: sirve hasta que haya cuentas de usuario.
- **Límite real:** el código del frontend viaja al navegador y no se puede ocultar. Lo que sí se protege es la API, los
  datos y, cuando se implemente, la lógica con LLM, que debe vivir solo en el servidor tras la clave o la cuenta.
- **Pendiente (decisión tuya):** pasar el repositorio a privado y retirar la demo de GitHub Pages, que publica todo el
  frontend; y añadir cuentas con usuario y contraseña (ver `docs/PRICING.md` para los planes).
