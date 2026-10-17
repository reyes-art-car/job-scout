from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from job_tracker.api.routers import health, offers
from job_tracker.config import get_settings
from job_tracker.infrastructure.db import models  # noqa: F401  (registra las tablas en Base)
from job_tracker.infrastructure.db.base import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Proyecto de un solo usuario sobre SQLite: crear las tablas al arrancar evita un paso manual.
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Job Hunter API", version="0.1.0", lifespan=lifespan)

    # CORS restringido explícitamente al origen del frontend en local — nunca "*",
    # para no abrir la API a cualquier página que el navegador visite.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type"],
    )

    app.include_router(health.router)
    app.include_router(offers.router)

    return app


app = create_app()
