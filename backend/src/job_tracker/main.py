import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from job_tracker.api.deps import get_current_user
from job_tracker.api.error_handlers import UnhandledErrorMiddleware, register_error_handlers
from job_tracker.api.routers import auth, health, offers, profile, searches
from job_tracker.api.security.body_limit import BodySizeLimitMiddleware
from job_tracker.api.security.headers import SecurityHeadersMiddleware
from job_tracker.api.security.rate_limit import Limits, RateLimitMiddleware
from job_tracker.config import Settings, get_settings
from job_tracker.infrastructure.db import models  # noqa: F401  (registra las tablas en Base)
from job_tracker.infrastructure.db.base import Base, engine

logger = logging.getLogger("job_tracker")

DOCS_PATHS = ("/docs", "/redoc", "/openapi.json")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Crear las tablas al arrancar evita un paso manual en desarrollo; en producción usa Postgres + migraciones.
    Base.metadata.create_all(bind=engine)
    if app.state.settings.app_env == "development":
        logger.warning("JWT_SECRET no configurado: se usa uno aleatorio y las sesiones no sobreviven al reinicio.")
    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    docs = settings.docs_enabled
    app = FastAPI(
        title="Job Hopping & Learning API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if docs else None,
        redoc_url=None,
        openapi_url="/openapi.json" if docs else None,
    )
    app.state.settings = settings

    # `add_middleware` apila hacia fuera: el último añadido recibe antes la petición.
    # Orden final (de fuera a dentro): cabeceras → errores no controlados → CORS → hosts → ritmo → tamaño de cuerpo.
    # CORS queda por fuera del límite de ritmo para que hasta un 429 lleve sus cabeceras CORS.
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=settings.max_body_bytes)
    app.add_middleware(
        RateLimitMiddleware,
        limits=Limits(
            reads=settings.rate_limit_per_minute,
            writes=settings.rate_limit_writes_per_minute,
            exports=settings.rate_limit_exports_per_minute,
            auth=settings.rate_limit_auth_per_minute,
        ),
        trust_proxy=settings.trust_proxy,
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts_list)
    # CORS cerrado a los orígenes configurados (nunca "*") y sin cookies: la autenticación va por cabecera.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH"],
        allow_headers=["Content-Type", "Authorization"],
        max_age=600,
    )
    app.add_middleware(UnhandledErrorMiddleware)
    app.add_middleware(
        SecurityHeadersMiddleware,
        hsts=settings.app_env == "production",
        relaxed_paths=DOCS_PATHS if docs else (),
    )

    register_error_handlers(app)

    app.include_router(health.router)
    # Denegado por defecto: solo /api/health, el registro y el login son públicos.
    app.include_router(auth.public_router)
    app.include_router(auth.router)
    app.include_router(profile.router)
    app.include_router(searches.router)
    app.include_router(offers.router, dependencies=[Depends(get_current_user)])
    return app


app = create_app()
