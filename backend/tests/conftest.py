import re
from collections.abc import Callable, Generator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from job_tracker.config import Settings
from job_tracker.domain.user.entities import User
from job_tracker.infrastructure.db import models  # noqa: F401  (registra las tablas)
from job_tracker.infrastructure.db.base import Base, get_db_session
from job_tracker.infrastructure.db.sqlalchemy_offer_repository import SqlAlchemyOfferRepository
from job_tracker.infrastructure.db.sqlalchemy_user_repository import SqlAlchemyUserRepository
from job_tracker.main import create_app

TEST_JWT_SECRET = "j" * 40
TEST_PASSWORD = "contraseña-de-prueba-1"
TOKEN_IN_LINK = re.compile(r"token=([A-Za-z0-9_\-.]+)")


class Outbox:
    """Sustituye al servicio de correo: guarda lo enviado para que las pruebas abran los enlaces."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []

    def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append((to, subject, body))

    def to(self, email: str) -> list[tuple[str, str, str]]:
        return [mail for mail in self.sent if mail[0] == email.lower()]

    def last_token(self, email: str) -> str:
        for _, _, body in reversed(self.to(email)):
            match = TOKEN_IN_LINK.search(body)
            if match:
                return match.group(1)
        raise AssertionError(f"No hay ningún enlace con token enviado a {email}")


@pytest.fixture
def session() -> Generator[Session, None, None]:
    """BD SQLite en memoria, aislada por test."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    with sessionmaker(bind=engine, autoflush=False)() as db:
        yield db
    engine.dispose()


@pytest.fixture
def make_user(session: Session) -> Callable[[str], User]:
    """Crea una cuenta directamente en la BD (sin pasar por la API)."""

    def factory(email: str = "ana@example.com") -> User:
        return SqlAlchemyUserRepository(session).add(User(id=None, email=email, password_hash="x"))

    return factory


@pytest.fixture
def repository(session: Session, make_user: Callable[[str], User]) -> SqlAlchemyOfferRepository:
    return SqlAlchemyOfferRepository(session, make_user().id or 0)


@pytest.fixture
def make_app(session: Session, tmp_path: Path) -> Callable[..., FastAPI]:
    """Fábrica de apps con ajustes a medida; nunca lee el .env real ni toca la BD real."""

    def factory(**overrides: object) -> FastAPI:
        values: dict[str, object] = {
            "jwt_secret": TEST_JWT_SECRET,
            "cv_output_dir": tmp_path / "cvs",
            "rate_limit_per_minute": 10_000,
            "rate_limit_writes_per_minute": 10_000,
            "rate_limit_exports_per_minute": 10_000,
            "rate_limit_auth_per_minute": 10_000,
        }
        values.update(overrides)
        app = create_app(Settings(_env_file=None, **values))  # type: ignore[arg-type]
        app.dependency_overrides[get_db_session] = lambda: session
        app.state.email_sender = Outbox()
        return app

    return factory


def outbox_of(client: TestClient) -> Outbox:
    sender = client.app.state.email_sender  # type: ignore[attr-defined]
    assert isinstance(sender, Outbox)
    return sender


def register(client: TestClient, email: str = "ana@example.com", *, verify: bool = True) -> dict[str, str]:
    """Crea la cuenta por la API (como haría un usuario: registro, enlace del correo, login) y devuelve la sesión."""
    response = client.post("/api/auth/register", json={"email": email, "password": TEST_PASSWORD})
    assert response.status_code == 202, response.text
    if verify:
        token = outbox_of(client).last_token(email)
        assert client.post("/api/auth/verify-email", json={"token": token}).status_code == 204
    login = client.post("/api/auth/login", json={"email": email, "password": TEST_PASSWORD})
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.fixture
def anon_client(make_app: Callable[..., FastAPI]) -> TestClient:
    """Cliente sin sesión. Sin `with`: no se ejecuta el lifespan, que crearía tablas en la BD real."""
    return TestClient(make_app(), raise_server_exceptions=False)


@pytest.fixture
def make_client(make_app: Callable[..., FastAPI]) -> Callable[..., TestClient]:
    """Cliente ya autenticado como un usuario recién registrado, sobre una app con los ajustes indicados."""

    def factory(email: str = "ana@example.com", **overrides: object) -> TestClient:
        # raise_server_exceptions=False: se prueba la respuesta 500 real que vería un cliente.
        client = TestClient(make_app(**overrides), raise_server_exceptions=False)
        client.headers.update(register(client, email))
        return client

    return factory


@pytest.fixture
def client(make_client: Callable[..., TestClient]) -> TestClient:
    return make_client()


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
