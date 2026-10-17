from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from job_tracker.api.deps import get_db_session
from job_tracker.infrastructure.db import models  # noqa: F401  (registra las tablas)
from job_tracker.infrastructure.db.base import Base
from job_tracker.infrastructure.db.sqlalchemy_offer_repository import SqlAlchemyOfferRepository
from job_tracker.main import create_app


@pytest.fixture
def session() -> Generator[Session, None, None]:
    """BD SQLite en memoria, aislada por test."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    with sessionmaker(bind=engine, autoflush=False)() as db:
        yield db
    engine.dispose()


@pytest.fixture
def repository(session: Session) -> SqlAlchemyOfferRepository:
    return SqlAlchemyOfferRepository(session)


@pytest.fixture
def client(session: Session) -> TestClient:
    # Sin `with`: no se ejecuta el lifespan, que crearía tablas en la BD real.
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: session
    return TestClient(app)


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
