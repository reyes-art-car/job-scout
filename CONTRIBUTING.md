# Guía de contribución

## Convención de mensajes de commit

```
tipo(ámbito): descripción breve en imperativo
```

- **tipo** (obligatorio): `feat`, `fix`, `refactor`, `docs`, `style`, `test`, `chore`, `perf`, `build`, `ci`, `security`
- **ámbito** (opcional): `backend`, `frontend`, `automation`, `docs`, `infra`…
- **descripción**: en minúscula, sin punto final, en imperativo («corrige», no «corregido»)

Ejemplos:

```
feat(backend): añade la exportación de ofertas a CSV
fix(frontend): corrige el filtro de compatibilidad mínima
security(api): limita el tamaño del cuerpo de las peticiones
```

## Activar los controles locales (una vez por clon)

```bash
git config core.hooksPath .githooks
git config commit.template .gitmessage
```

- `commit-msg` valida el formato del mensaje.
- `pre-commit` bloquea ficheros privados (`.env`, CVs, Excel, `candidate_profile.yaml`…) y patrones de claves.

## Antes de abrir un pull request

```bash
# Backend
cd backend
pip install -r requirements-dev.txt && pip install -e .
ruff check src tests scripts && ruff format --check src tests scripts
mypy
bandit -q -r src
pytest -q --cov=job_tracker --cov-fail-under=85

# Automatización
cd ../automation && pip install -r requirements.txt pytest ruff && ruff check . && pytest -q

# Frontend
cd ../frontend && npm ci && npx ng lint && npx ng test --watch=false --browsers=ChromeHeadless && npx ng build
```

## Principios de código

- **Dependencias hacia el dominio.** El dominio no importa FastAPI, SQLAlchemy ni Pydantic. Los casos de uso
  dependen de puertos pequeños (`OfferReader`, `OfferWriter`…), no del repositorio completo.
- **Rutas finas.** Una ruta valida, llama a un caso de uso y devuelve. Sin lógica de negocio ni `try/except` de
  errores de dominio: de eso se encargan los manejadores de `api/error_handlers.py`.
- **Los datos de fuera no son de fiar** (peticiones, Excel, salida del LLM, `localStorage`): se validan y sanean en
  el borde, y cada defensa lleva su prueba.
- **Sin números mágicos**: umbrales y límites son constantes con nombre y comentario.
- **Una prueba por comportamiento**, con el nombre de lo que garantiza.
