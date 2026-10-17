# Arquitectura

JobHunter son tres piezas que comparten un único modelo de oferta (`Offer`):

```mermaid
flowchart LR
    subgraph Captura
        A[automation/jobsearch<br/>Claude Code + rúbrica de 100 pts] -->|valida y sanea| X[(Ofertas_*.xlsx)]
    end
    X -->|scripts/seed.py| DB[(SQLite)]
    subgraph Backend · FastAPI
        M[middleware<br/>cabeceras · ritmo · tamaño] --> R[api/routers<br/>+ token]
        R --> U[application<br/>casos de uso] --> P{{domain<br/>puertos}}
        P -.implementa.-> I[infrastructure<br/>SQLAlchemy · Excel · ficheros]
        I --> DB
    end
    subgraph Frontend · Angular 20
        S[OfferStore<br/>signals] --> G{{OfferGateway}}
        G --> GA[ApiOfferGateway]
        G --> GD[DemoOfferGateway]
        S --> V[Panel · Ofertas · Adaptar CV<br/>Carta · Brecha de skills]
        V --> C[core: análisis · adaptación · carta<br/>funciones puras]
    end
    GA -- "/api + Bearer" --> M
    GD -.-> D[data/demo/*.json + localStorage]
```

## Principios SOLID aplicados

| Principio | Dónde se ve |
|---|---|
| **S** · Responsabilidad única | Un caso de uso por clase (`CreateOffer`, `UpdateOffer`, `GetOfferCv`…). Las rutas solo validan, delegan y devuelven; el mapeo de errores vive en `error_handlers.py`; el saneado en `shared/sanitize.py`; el acceso seguro a ficheros en `DirectoryCvLocator`. En el frontend, `Offers` coordina y delega en `OfferForm`, `KanbanBoard` y la función pura `applyQuery`. El buscador diario se dividió de un script de 700 líneas en `config`, `prompt`, `llm`, `parsing`, `offer`, `excel_store`, `cv_docx`, `reporting` y `cli` |
| **O** · Abierto/cerrado | Añadir un portal de búsqueda es añadir una entrada a `STRATEGIES` (antes, otra rama de un `if/elif`). Añadir un origen de datos en el frontend es una nueva clase `OfferGateway`. Las columnas del CSV son datos (`COLUMNS`), no código |
| **L** · Sustitución de Liskov | Cualquier `OfferGateway` (API o demo) o `LlmClient` (Claude Code o un doble de pruebas) puede usarse donde se espera el tipo base sin que el consumidor lo note |
| **I** · Segregación de interfaces | `OfferRepository` se divide en `OfferReader`, `OfferWriter`, `OfferStatsReader` y `OfferIdentity`; cada caso de uso depende solo de lo que usa (`GetOffer` ni ve cómo se escribe) |
| **D** · Inversión de dependencias | El dominio no importa FastAPI, SQLAlchemy ni Pydantic. Las dependencias de FastAPI devuelven el **puerto** (`OfferRepository`), no el adaptador. `OfferStore` depende de la clase abstracta `OfferGateway`; `run_search` recibe el cliente del modelo, las rutas y el perfil por parámetro |

Otras prácticas de código limpio: constantes con nombre en lugar de números mágicos (`HIGH_PRIORITY_THRESHOLD`,
`MAX_ROWS`, `BACKEND_MAX_FRONT_RATIO`…), una sola fuente para reglas repetidas (`priority_for`), tipado estricto
(`mypy --strict` en el backend, `strict` en TypeScript y sin `any`/`$any`) y linters como parte del CI.

## Backend (`backend/`)

Arquitectura hexagonal con dependencias que apuntan siempre hacia el dominio:

| Capa | Contenido | Depende de |
|---|---|---|
| `domain/` | Entidades (`Offer`, `InterviewSession`), puertos segregados, `scoring`, excepciones | nada |
| `application/` | Casos de uso: listar, obtener, crear, editar, cambiar estado, descargar CV, exportar CSV | `domain` |
| `infrastructure/` | Adaptadores: repositorio SQLAlchemy, importador de Excel y JSON, localizador de ficheros | `domain` |
| `api/` | Routers, esquemas Pydantic con saneado, manejadores de error, middleware de seguridad | `application` |
| `shared/` | Saneado de texto no confiable (lo usan la API, el importador y el buscador) | — |

Decisiones:

- **Los tests de la API sustituyen la sesión** por una SQLite en memoria con `dependency_overrides`, y construyen la app con `create_app(settings)`: nunca leen el `.env` real ni tocan la base de datos real.
- **Importación idempotente**: se deduplica por ID y por URL, de modo que `seed.py` se puede ejecutar varias veces.
- **Denegado por defecto**: el token se exige a nivel de router; una ruta nueva queda protegida sin hacer nada. Un test recorre todas las rutas para garantizarlo.
- **Configuración que falla pronto**: en producción la aplicación no arranca sin token fuerte ni con CORS `*`.

Endpoints: `GET /api/offers` (filtros y paginación), `POST /api/offers`, `GET /api/offers/{id}`, `PATCH /api/offers/{id}` y `/status`, `GET /api/offers/stats`, `GET /api/offers/export.csv`, `GET /api/offers/{id}/cv`, `GET /api/health` (público). Documentación interactiva en `/docs` solo en desarrollo.

## Frontend (`frontend/`)

Angular 20 con componentes *standalone*, `signals`, control de flujo nativo (`@if`, `@for`), `OnPush` en todos los componentes y carga diferida por ruta. Sin librerías de UI ni de gráficos: los diagramas son CSS y los iconos, SVG.

- **`core/offer.store.ts`**: estado de las ofertas. Delega el acceso a datos en un `OfferGateway`: `ApiOfferGateway` si la API responde con datos y `DemoOfferGateway` si no (con persistencia validada en `localStorage`). Por eso la misma aplicación funciona en local con backend y en GitHub Pages sin él.
- **`core/offer-validation.ts`**: valida y normaliza cualquier dato que venga de la red o del navegador antes de usarlo.
- **`core/auth.ts`**: token en `sessionStorage` y un interceptor que solo lo envía a `/api/`.
- **`core/tech-catalog.ts`**: catálogo de 64 tecnologías con expresiones regulares, nivel (`have` / `partial` / `gap`) y plan de aprendizaje.
- **`core/offer-analysis.ts`**: requisitos ponderados (obligatoria 3 · texto 1,5 · deseable 1), cobertura y rol detectado.
- **`core/tailoring.ts`**: reordena logros y competencias y redacta titular y resumen **solo con tecnologías acreditadas**.
- **`core/cover-letter.ts`**, **`core/export.ts`**: carta de presentación, CSV compatible con Excel y HTML que Word abre como documento.

## Automatización (`automation/`)

Paquete `jobsearch/` con `busqueda_diaria.py` como único punto de entrada:

```
prompt.py       estrategias de búsqueda (general, LinkedIn, internacional) + prompts/search_prompt.txt
llm.py          puerto LlmClient y adaptador de Claude Code (solo WebSearch/WebFetch, prompt por stdin)
parsing.py      extrae el JSON de la respuesta del modelo
offer.py        valida y sanea cada oferta: la salida del modelo es entrada no confiable
excel_store.py  lee URLs conocidas y añade filas (siempre como texto)
cv_docx.py      genera el .docx dentro de la carpeta de CVs
cli.py          run_search(): una ejecución completa con todas las dependencias inyectadas
```

Se programa con el Programador de tareas de Windows (`tarea_busqueda_ofertas.xml`).

## Pruebas y calidad

| Capa | Herramientas | Qué cubre |
|---|---|---|
| Backend | pytest · ruff (incluye reglas de seguridad `S`) · `mypy --strict` · bandit · pip-audit | API completa, seguridad (auth, límites, saneado, ficheros, cabeceras), importadores, configuración |
| Automatización | pytest · ruff | Validación de la salida del modelo, Excel, CV, flujo completo con un cliente simulado |
| Frontend | Karma/Jasmine · ESLint (Angular + reglas de seguridad) | Validación de datos, almacén de ofertas, interceptor, análisis, adaptación, carta, exportación |

CI en GitHub Actions: `ci.yml` (todo lo anterior), `security.yml` (pip-audit, npm audit, gitleaks, semanal),
`codeql.yml` y `pages.yml` (demo). Dependabot semanal. Detalle de la seguridad en [SECURITY.md](SECURITY.md).

## Evidence-based search workspace

The frontend adds a local career workspace: `core/career.ts` contains matching, evidence, preference,
and date rules; `career-validation.ts` validates stored and imported data; `career.service.ts` owns
persistence and immutable CV snapshots. `MatchReview` explains and corrects requirement origins.
The profile, learning, CV, cover letter, dashboard, and application-history views share these rules.
`OfferStore` records a status transition only after the active gateway accepts it.

This workspace is browser-local and is not stored in SQLite or synchronized to the API. Demo and API
offer records have distinct keys. See [workflow, calculations, and limits](EVIDENCE_BASED_SEARCH.md).
