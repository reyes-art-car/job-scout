from collections.abc import Callable

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from job_tracker.domain.interview.entities import ChatMessage, ChatRole, GuidedMode, InterviewSession
from job_tracker.infrastructure.db.models import (
    ChatMessageModel,
    InterviewSessionModel,
    OfferModel,
    SearchJobModel,
    SearchProfileModel,
    UserModel,
)
from job_tracker.infrastructure.db.sqlalchemy_interview_repository import SqlAlchemyInterviewRepository
from tests.conftest import TEST_PASSWORD, register

PROFILE = {"headline": "Desarrolladora Java junior", "summary": "CFGS DAW con prácticas en Spring Boot."}
OFFER = {"title": "Java Junior", "company": "Acme", "url": "https://example.com/o/1", "compatibility": 80}


def _fill(client: TestClient, session: Session) -> None:
    """Deja datos de todos los tipos para esa cuenta: perfil, oferta, búsqueda y una sesión de entrevista."""
    client.put("/api/profile", json=PROFILE)
    client.post("/api/offers", json=OFFER)
    client.post("/api/searches", json={})
    user_id = session.query(UserModel).filter_by(email="ana@example.com").one().id
    interviews = SqlAlchemyInterviewRepository(session, user_id)
    created = interviews.create_session(
        InterviewSession(id=None, mode=GuidedMode.TECHNICAL_QUESTION, offer_id=None, title="t")
    )
    interviews.add_message(ChatMessage(id=None, session_id=created.id or 0, role=ChatRole.USER, content="hola"))


def _rows(session: Session) -> dict[str, int]:
    models = (UserModel, SearchProfileModel, OfferModel, SearchJobModel, InterviewSessionModel, ChatMessageModel)
    return {model.__name__: session.query(model).count() for model in models}


# ── Exportación (acceso y portabilidad) ──────────────────────────────────────────


def test_export_contains_everything_the_service_stores_about_the_user(client: TestClient, session: Session) -> None:
    client.put("/api/profile", json=PROFILE)
    client.post("/api/offers", json=OFFER)
    client.put("/api/profile", json=PROFILE)
    body = client.get("/api/auth/export").json()
    assert body["account"]["email"] == "ana@example.com" and body["account"]["plan"] == "free"
    assert body["profile"]["headline"] == PROFILE["headline"]
    assert [o["title"] for o in body["offers"]] == ["Java Junior"]
    assert body["exported_at"]


def test_export_never_includes_the_password_hash_or_other_users_data(
    make_client: Callable[..., TestClient], offer_payload: dict
) -> None:
    ana = make_client("ana@example.com")
    ana.post("/api/offers", json=offer_payload)
    bea = TestClient(ana.app)
    bea.headers.update(register(bea, "bea@example.com"))
    text = bea.get("/api/auth/export").text
    assert "scrypt$" not in text and "password" not in text.lower()
    assert bea.get("/api/auth/export").json()["offers"] == []  # lo de Ana no aparece en la exportación de Bea


def test_export_requires_a_session(anon_client: TestClient) -> None:
    assert anon_client.get("/api/auth/export").status_code == 401


def test_export_has_its_own_strict_rate_limit(make_client: Callable[..., TestClient]) -> None:
    client = make_client(rate_limit_exports_per_minute=1)
    assert [client.get("/api/auth/export").status_code for _ in range(2)] == [200, 429]


# ── Borrado de cuenta (supresión) ────────────────────────────────────────────────


def test_deleting_the_account_removes_every_trace_of_it(client: TestClient, session: Session) -> None:
    _fill(client, session)
    assert all(count >= 1 for count in _rows(session).values())

    response = client.post("/api/auth/delete-account", json={"password": TEST_PASSWORD})
    assert response.status_code == 204
    assert _rows(session) == dict.fromkeys(_rows(session), 0)  # ni cuenta, ni perfil, ni ofertas, ni entrevistas


def test_deleting_one_account_leaves_the_others_untouched(
    make_client: Callable[..., TestClient], session: Session, offer_payload: dict
) -> None:
    ana = make_client("ana@example.com")
    bea = TestClient(ana.app)
    bea.headers.update(register(bea, "bea@example.com"))
    bea.put("/api/profile", json=PROFILE)
    bea.post("/api/offers", json=offer_payload)
    ana.post("/api/offers", json=offer_payload)

    assert ana.post("/api/auth/delete-account", json={"password": TEST_PASSWORD}).status_code == 204
    assert session.query(UserModel).count() == 1 and session.query(OfferModel).count() == 1
    assert bea.get("/api/offers").json()["total"] == 1 and bea.get("/api/profile").json() is not None


def test_a_deleted_account_cannot_log_in_nor_reuse_its_session(client: TestClient, anon_client: TestClient) -> None:
    client.post("/api/auth/delete-account", json={"password": TEST_PASSWORD})
    assert client.get("/api/auth/me").status_code == 401
    assert (
        client.post("/api/auth/login", json={"email": "ana@example.com", "password": TEST_PASSWORD}).status_code == 401
    )


def test_deleting_needs_the_right_password_and_a_wrong_one_keeps_everything(
    client: TestClient, session: Session
) -> None:
    _fill(client, session)
    before = _rows(session)
    wrong = client.post("/api/auth/delete-account", json={"password": "no-es-esta"})
    assert wrong.status_code == 403  # no es 401: la sesión es válida, no se debe confundir con «sesión caducada»
    assert _rows(session) == before
    assert client.get("/api/auth/me").status_code == 200


def test_wrong_passwords_on_delete_are_throttled_like_logins(make_app: Callable[..., FastAPI]) -> None:
    client = TestClient(make_app(login_failures_per_window=2))
    client.headers.update(register(client))
    codes = [client.post("/api/auth/delete-account", json={"password": "mal"}).status_code for _ in range(3)]
    assert codes == [403, 403, 429]
    assert client.post("/api/auth/delete-account", json={"password": TEST_PASSWORD}).status_code == 429


def test_deleting_requires_a_session_and_a_body(anon_client: TestClient, client: TestClient) -> None:
    assert anon_client.post("/api/auth/delete-account", json={"password": "x"}).status_code == 401
    assert client.post("/api/auth/delete-account", json={}).status_code == 422
    assert client.post("/api/auth/delete-account", json={"password": "x", "extra": 1}).status_code == 422
