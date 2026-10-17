# Arquitectura

JobHunter son tres piezas que comparten un único modelo de oferta (`Offer`):

```mermaid
flowchart LR
    subgraph Captura
        A[automation/busqueda_diaria.py<br/>Claude Code + rúbrica de 100 pts] -->|Excel| X[(Ofertas_*.xlsx)]
    end
    X -->|scripts/seed.py| DB[(SQLite)]
    subgraph Backend · FastAPI
        R[api/routers] --> U[application<br/>casos de uso] --> P{{domain<br/>puertos}}
        P -.implementa.-> I[infrastructure<br/>SQLAlchemy · Excel · LLM]
        I --> DB
    end
    subgraph Frontend · Angular 20
        S[OfferStore<br/>signals] --> V[Panel · Ofertas · Adaptar CV<br/>Carta · Brecha de skills]
        C[core/tailoring · tech-catalog<br/>funciones puras]
        V --> C
    end
    S -- "/api (proxy)" --> R
    S -. sin API .-> D[data/demo/*.json + localStorage]
```

## Backend (`backend/`)

Arquitectura hexagonal con dependencias que apuntan siempre hacia el dominio:

| Capa | Contenido | Depende de |
|---|---|---|
| `domain/` | Entidades (`Offer`, `InterviewSession`), puertos (`OfferRepository`), excepciones | nada |
| `application/` | Casos de uso: `ListOffers`, `GetOffer`, `CreateOffer`, `UpdateOfferStatus`, exportación a CSV | `domain` |
| `infrastructure/` | Adaptadores: repositorio SQLAlchemy, importador de Excel y JSON | `domain` |
| `api/` | Routers FastAPI, esquemas Pydantic, inyección de dependencias | `application` |

Decisiones:

- **El dominio no conoce SQLAlchemy ni Pydantic.** Los tests de la API sustituyen la sesión por una SQLite en memoria con `dependency_overrides`, sin tocar la base de datos real.
- **Importación idempotente**: se deduplica por ID y por URL, de modo que `seed.py` se puede ejecutar varias veces.
- **CORS cerrado** al origen del frontend, nunca `*`. El nombre del CV a descargar se normaliza con `basename` para evitar *path traversal*.
- **CSV seguro**: las celdas que empiezan por `=`, `+`, `-` o `@` se neutralizan para evitar inyección de fórmulas al abrirlo en Excel.

Endpoints: `GET /api/offers` (filtros y paginación), `POST /api/offers`, `GET /api/offers/{id}`, `PATCH /api/offers/{id}` y `/status`, `GET /api/offers/stats`, `GET /api/offers/export.csv`, `GET /api/offers/{id}/cv`, `GET /api/health`. Documentación interactiva en `/docs`.

## Frontend (`frontend/`)

Angular 20 con componentes *standalone*, `signals`, control de flujo nativo (`@if`, `@for`), `OnPush` en todos los componentes y carga diferida por ruta. Sin librerías de UI ni de gráficos: los diagramas son CSS y los iconos, SVG.

- **`core/offer.store.ts`**: única fuente de datos. Intenta la API (`/api`); si no responde en 2,5 s cae a `data/demo/` y persiste en `localStorage`. Por eso la misma aplicación funciona en local con backend y en GitHub Pages sin él.
- **`core/tech-catalog.ts`**: catálogo de 64 tecnologías con expresiones regulares, nivel (`have` / `partial` / `gap`) y plan de aprendizaje.
- **`core/tailoring.ts`**: funciones puras que convierten una oferta en requisitos ponderados (obligatoria 3 · texto 1,5 · deseable 1), detectan el rol (backend / full stack / frontend), reordenan logros y competencias y redactan titular y resumen **solo con tecnologías acreditadas**.
- **`core/cover-letter.ts`**, **`core/export.ts`**: carta de presentación, CSV compatible con Excel y HTML que Word abre como documento.

## Automatización (`automation/`)

`busqueda_diaria.py` construye un prompt para Claude Code con el perfil, las reglas de exclusión, la rúbrica de 100 puntos y un esquema JSON de salida; añade las ofertas nuevas al Excel (sin duplicar URLs) y genera un CV adaptado por cada una con ≥ 65 % de compatibilidad. Se programa con el Programador de tareas de Windows (`tarea_busqueda_ofertas.xml`).

## Pruebas

| Capa | Herramienta | Qué cubre |
|---|---|---|
| Backend | pytest + TestClient | API completa (alta, filtros, estado, CSV, 404/409/422), importadores y deduplicación |
| Frontend | Karma + Jasmine | Detección de tecnologías, análisis de ofertas, adaptación del CV, carta, exportación CSV |

CI en GitHub Actions (`.github/workflows/ci.yml`) y despliegue de la demo en GitHub Pages (`pages.yml`).
