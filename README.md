# JobHunter

**Gestor de búsqueda de empleo IT**: recopila ofertas, las puntúa frente a tu perfil, adapta el currículum a cada una, genera la carta de presentación y te dice qué tecnologías te faltan.

[![CI](https://github.com/reyes-art-car/job-scout/actions/workflows/ci.yml/badge.svg)](https://github.com/reyes-art-car/job-scout/actions/workflows/ci.yml)
![Angular](https://img.shields.io/badge/Angular-20-DD0031?logo=angular&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6?logo=typescript&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![Tests](https://img.shields.io/badge/tests-14%20backend%20%C2%B7%2025%20frontend-1b7a4b)

**[▶ Probar la demo](https://reyes-art-car.github.io/job-scout/)** · funciona sin servidor, con datos de ejemplo y sin registrarse.

![Panel de búsqueda](docs/screenshots/panel.png)

## Qué hace

| Sección | Qué resuelve |
|---|---|
| **Panel** | Indicadores del pipeline, embudo de candidaturas, distribución por compatibilidad y las tecnologías más pedidas |
| **Ofertas** | Tabla y tablero Kanban con arrastrar y soltar, filtros, alta manual con estimación automática y exportación a Excel (CSV) |
| **Adaptar CV** | Detecta las tecnologías de la oferta, reordena logros y competencias, propone titular y resumen y exporta a Word o PDF. **Solo usa lo que el perfil acredita** |
| **Carta de presentación** | Carta editable a partir de la oferta y el perfil, en tono formal o cercano, con opción de mencionar con honestidad lo que aún no has usado |
| **Brecha de skills** | Qué piden las ofertas y no figura en el CV, con prioridad, ofertas que desbloquea cada tecnología y cómo acreditarla |

<table>
  <tr>
    <td><img src="docs/screenshots/ofertas.png" alt="Ofertas"></td>
    <td><img src="docs/screenshots/adaptar-cv.png" alt="Adaptar CV"></td>
  </tr>
</table>

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | Angular 20 · TypeScript · signals · componentes standalone · SCSS · Karma/Jasmine |
| Backend | Python 3.13 · FastAPI · Pydantic · SQLAlchemy 2 · SQLite · pytest |
| Automatización | Claude Code (búsqueda diaria con rúbrica de 100 puntos) · openpyxl · python-docx |
| Calidad | GitHub Actions (tests + build) · despliegue de la demo en GitHub Pages |

## Decisiones de diseño

- **Arquitectura hexagonal en el backend**: el dominio no depende de SQLAlchemy ni de FastAPI y los casos de uso se prueban sin base de datos. [Detalle](docs/ARCHITECTURE.md).
- **Un solo frontend, dos fuentes de datos**: usa la API si responde y, si no, los datos de demostración con persistencia en el navegador. Por eso la demo en GitHub Pages es totalmente interactiva.
- **La lógica de adaptación son funciones puras** (`core/tailoring.ts`) con tests: sin red, sin estado y sin inventar tecnologías que el perfil no acredita.
- **Seguridad básica desde el principio**: CORS cerrado, protección frente a *path traversal* en la descarga de CVs, neutralización de fórmulas en el CSV y validación estricta de entradas.

## Ejecutarlo en local

Requisitos: Node 22 y Python 3.11 o superior.

```bash
# 1) Backend (opcional: sin él, el frontend funciona en modo demo)
cd backend
python -m venv .venv && .venv\Scripts\activate        # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt && pip install -e .
python scripts/seed.py --demo                         # carga las ofertas de ejemplo
uvicorn job_tracker.main:app --reload                 # http://localhost:8000/docs

# 2) Frontend
cd frontend
npm ci
npm start                                             # http://localhost:4200 (proxy a /api)
```

Importar tu propio Excel: `python scripts/seed.py --excel ruta/Ofertas.xlsx`.

### Tests

```bash
cd backend  && pytest -q                                        # 14 pruebas
cd frontend && npx ng test --watch=false --browsers=ChromeHeadless   # 25 pruebas
```

## Estructura

```
├── frontend/          Angular 20 (panel, ofertas, adaptar CV, carta, brecha de skills)
├── backend/           FastAPI · domain / application / infrastructure / api · tests
├── automation/        Búsqueda diaria de ofertas con Claude Code + tarea programada de Windows
├── data/demo/         Ofertas y perfil de demostración (datos públicos de anuncios)
├── docs/              Arquitectura, hoja de ruta, informe de búsqueda y brecha de skills
└── .github/workflows/ CI y despliegue de la demo
```

## Documentación

- [Arquitectura](docs/ARCHITECTURE.md)
- [Hoja de ruta y sugerencias](docs/ROADMAP.md)
- [Brecha de skills (análisis de mercado)](docs/SKILLS_GAP.md)
- [Informe de búsqueda de ofertas, 17/10/2026](docs/BUSQUEDA_2026-10-17.md)

## Privacidad

Los currículums, las cartas, los Excel de ofertas, los registros y el perfil con datos de contacto **no se versionan** (ver `.gitignore`). El repositorio solo contiene datos de demostración procedentes de anuncios públicos. Para usar tu propio perfil, copia `backend/config/candidate_profile.example.yaml` a `candidate_profile.yaml`.

## English summary

JobHunter is a full-stack job-search assistant: it collects job offers, scores them against a candidate profile, tailors the CV and cover letter to each offer using only skills the profile actually proves, and reports the technology gap against the market. Angular 20 + TypeScript frontend, FastAPI backend with hexagonal architecture, pytest and Karma test suites, CI and a live demo on GitHub Pages.

## Autora

**María Reyes Artacho Carrero** · Desarrolladora full-stack junior (Java · Spring Boot · Angular) · Sevilla
[LinkedIn](https://www.linkedin.com/in/maria-reyes-a-carrero/) · [mariareyesartcar+github@gmail.com](mailto:mariareyesartcar+github@gmail.com)

Licencia [MIT](LICENSE).
