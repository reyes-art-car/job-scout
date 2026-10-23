# Backend · Job Hopping & Learning API

FastAPI con arquitectura hexagonal. Ver [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md).

```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements-dev.txt && pip install -e .
cp .env.example .env                    # JWT_SECRET y ANTHROPIC_API_KEY obligatorios con APP_ENV=production (ver docs/SECURITY.md)
python scripts/seed.py --demo           # o: --excel ../Ofertas_Maria_Reyes.xlsx
uvicorn job_tracker.main:app --reload   # documentación interactiva en http://localhost:8000/docs
pytest -q --cov=job_tracker
ruff check src tests scripts && ruff format --check src tests scripts
mypy && bandit -q -r src
```

| Carpeta | Contenido |
|---|---|
| `src/job_tracker/domain` | Entidades, puertos y excepciones (sin dependencias de framework) |
| `src/job_tracker/application` | Casos de uso |
| `src/job_tracker/infrastructure` | SQLAlchemy, importadores de Excel y JSON |
| `src/job_tracker/api` | Routers, esquemas y dependencias de FastAPI |
| `config/` | `candidate_profile.example.yaml` (plantilla; el real está ignorado por git) |
| `tests/` | `unit/` e `integration/`, con SQLite en memoria |

Las tablas se crean al arrancar. `alembic/` está preparado para cuando el esquema deba migrarse.
