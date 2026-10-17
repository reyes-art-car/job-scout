from collections.abc import Callable, Generator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from job_tracker.config import Settings
from job_tracker.infrastructure.db import models  # noqa: F401  (registra las tablas)
from job_tracker.infrastructure.db.base import Base, get_db_session
from job_tracker.infrastructure.db.sqlalchemy_offer_repository import SqlAlchemyOfferRepository
from job_tracker.main import create_app

TEST_TOKEN = "t" * 40


@pytest.fixture
def session() -> Generator[Session, None, None]:
    """BD SQLite en memoria, aislada por test."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    with sessionmaker(bind=engine, autoflush=False)() as db:
        yield db
    engine.dispose()


@pytest.fixture
def repository(session: Session) -> SqlAlchemyOfferRepository:
    return SqlAlchemyOfferRepository(session)


@pytest.fixture
def make_app(session: Session, tmp_path: Path) -> Callable[..., FastAPI]:
    """Fábrica de apps con ajustes a medida; nunca lee el .env real ni toca la BD real."""

    def factory(**overrides: object) -> FastAPI:
        values: dict[str, object] = {
            "cv_output_dir": tmp_path / "cvs",
            "rate_limit_per_minute": 10_000,
            "rate_limit_writes_per_minute": 10_000,
            "rate_limit_exports_per_minute": 10_000,
        }
        values.update(overrides)
        app = create_app(Settings(_env_file=None, **values))  # type: ignore[arg-type]
        app.dependency_overrides[get_db_session] = lambda: session
        return app

    return factory


@pytest.fixture
def client(make_app: Callable[..., FastAPI]) -> TestClient:
    # Sin `with`: no se ejecuta el lifespan, que crearía tablas en la BD real.
    # raise_server_exceptions=False: se prueba la respuesta 500 real que vería un cliente.
    return TestClient(make_app(), raise_server_exceptions=False)


@pytest.fixture
def secured_client(make_app: Callable[..., FastAPI]) -> TestClient:
    return TestClient(make_app(api_token=TEST_TOKEN), raise_server_exceptions=False)


@pytest.fixture
def offer_payload() -> dict:
    return {
        "title": "Junior Java Developer",
        "company": "Acme",
        "portal": "Tecnoempleo",
        "url": "https://example.com/oferta-1",
        "location": "Sevilla",
        "modality": "Remoto 100%",
        "mandatory_tech": "Java, Spring Boot",
        "compatibility": 80,
    }
