# Backend · Job Hunter API

FastAPI con arquitectura hexagonal. Ver [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md).

```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt && pip install -e .
cp .env.example .env                    # solo hace falta ANTHROPIC_API_KEY para las funciones con LLM
python scripts/seed.py --demo           # o: --excel ../Ofertas_Maria_Reyes.xlsx
uvicorn job_tracker.main:app --reload   # documentación interactiva en http://localhost:8000/docs
pytest -q
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
