from collections.abc import Callable

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from job_tracker.infrastructure.security.tokens import (
    RESET_LINK,
    VERIFY_EMAIL,
    create_access_token,
    create_action_token,
)
from tests.conftest import TEST_JWT_SECRET, TEST_PASSWORD, outbox_of, register

PROFILE = {"headline": "Desarrolladora Java junior", "summary": "CFGS DAW con prácticas en Spring Boot."}
EMAIL = "ana@example.com"
NEW_PASSWORD = "otra-contraseña-larga-2"


def _login(client: TestClient, password: str = TEST_PASSWORD) -> int:
    return client.post("/api/auth/login", json={"email": EMAIL, "password": password}).status_code


# ── Verificación de email ────────────────────────────────────────────────────────


def test_register_returns_no_session_and_sends_a_confirmation_link(anon_client: TestClient) -> None:
    response = anon_client.post("/api/auth/register", json={"email": EMAIL, "password": TEST_PASSWORD})
    assert response.status_code == 202 and "access_token" not in response.text
    [(to, subject, body)] = outbox_of(anon_client).to(EMAIL)
    assert to == EMAIL and "Confirma" in subject and "/#/verificar?token=" in body


def test_register_response_is_identical_whether_or_not_the_email_exists(anon_client: TestClient) -> None:
    first = anon_client.post("/api/auth/register", json={"email": EMAIL, "password": TEST_PASSWORD})
    again = anon_client.post("/api/auth/register", json={"email": "ANA@example.com", "password": "x" * 12})
    assert (first.status_code, first.json()) == (again.status_code, again.json())
    # Quien ya tenía la cuenta recibe un aviso en su bandeja; su contraseña NO cambia.
    assert "Ya tienes una cuenta" in outbox_of(anon_client).to(EMAIL)[-1][1]
    assert _login(anon_client) == 200 and _login(anon_client, "x" * 12) == 401


def test_unverified_accounts_can_log_in_but_cannot_search(anon_client: TestClient) -> None:
    headers = register(anon_client, verify=False)
    assert anon_client.get("/api/auth/me", headers=headers).json()["email_verified"] is False
    anon_client.put("/api/profile", json=PROFILE, headers=headers)
    blocked = anon_client.post("/api/searches", json={}, headers=headers)
    assert blocked.status_code == 403 and "email" in blocked.json()["error"]

    token = outbox_of(anon_client).last_token(EMAIL)
    assert anon_client.post("/api/auth/verify-email", json={"token": token}).status_code == 204
    assert anon_client.post("/api/searches", json={}, headers=headers).status_code == 202


def test_verification_link_can_be_resent_but_not_flooded(anon_client: TestClient) -> None:
    headers = register(anon_client, verify=False)
    for _ in range(5):
        assert anon_client.post("/api/auth/resend-verification", headers=headers).status_code == 202
    # 1 del registro + los reenvíos hasta el tope de 3 correos por dirección y hora.
    assert len(outbox_of(anon_client).to(EMAIL)) == 3


def test_resend_does_nothing_once_verified(anon_client: TestClient) -> None:
    headers = register(anon_client)
    before = len(outbox_of(anon_client).to(EMAIL))
    anon_client.post("/api/auth/resend-verification", headers=headers)
    assert len(outbox_of(anon_client).to(EMAIL)) == before


@pytest.mark.parametrize("kind", ["garbage", "expired", "wrong_type", "other_secret"])
def test_invalid_verification_links_are_rejected(anon_client: TestClient, kind: str) -> None:
    register(anon_client, verify=False)
    tokens = {
        "garbage": "esto.no.es-un-token",
        "expired": create_action_token(VERIFY_EMAIL, 1, secret=TEST_JWT_SECRET, minutes=-1),
        "wrong_type": create_access_token(1, secret=TEST_JWT_SECRET, minutes=5),  # una sesión no sirve de enlace
        "other_secret": create_action_token(VERIFY_EMAIL, 1, secret="otro-" + "x" * 40, minutes=5),
    }
    assert anon_client.post("/api/auth/verify-email", json={"token": tokens[kind]}).status_code == 400
    assert anon_client.get("/api/auth/me").status_code == 401  # nadie quedó autenticado por el intento


def test_email_links_cannot_be_used_as_sessions(anon_client: TestClient) -> None:
    register(anon_client)
    for kind in (VERIFY_EMAIL, RESET_LINK):
        link_token = create_action_token(kind, 1, secret=TEST_JWT_SECRET, minutes=5)
        assert anon_client.get("/api/offers", headers={"Authorization": f"Bearer {link_token}"}).status_code == 401


# ── Recuperar contraseña ─────────────────────────────────────────────────────────


def test_forgot_password_answers_the_same_for_unknown_emails_and_sends_nothing(anon_client: TestClient) -> None:
    register(anon_client)
    known = anon_client.post("/api/auth/forgot-password", json={"email": EMAIL})
    unknown = anon_client.post("/api/auth/forgot-password", json={"email": "nadie@example.com"})
    assert (known.status_code, known.json()) == (unknown.status_code, unknown.json())
    assert outbox_of(anon_client).to("nadie@example.com") == []
    assert "Restablece" in outbox_of(anon_client).to(EMAIL)[-1][1]


def test_password_reset_changes_the_password_and_kills_old_sessions(anon_client: TestClient) -> None:
    old_session = register(anon_client)
    anon_client.post("/api/auth/forgot-password", json={"email": EMAIL})
    token = outbox_of(anon_client).last_token(EMAIL)

    done = anon_client.post("/api/auth/reset-password", json={"token": token, "password": NEW_PASSWORD})
    assert done.status_code == 204
    assert _login(anon_client, TEST_PASSWORD) == 401 and _login(anon_client, NEW_PASSWORD) == 200
    assert anon_client.get("/api/auth/me", headers=old_session).status_code == 401  # sesión robada, sesión muerta


def test_reset_link_works_only_once(anon_client: TestClient) -> None:
    register(anon_client)
    anon_client.post("/api/auth/forgot-password", json={"email": EMAIL})
    token = outbox_of(anon_client).last_token(EMAIL)
    assert (
        anon_client.post("/api/auth/reset-password", json={"token": token, "password": NEW_PASSWORD}).status_code == 204
    )
    again = anon_client.post("/api/auth/reset-password", json={"token": token, "password": "tercera-clave-larga-3"})
    assert again.status_code == 400
    assert _login(anon_client, NEW_PASSWORD) == 200


def test_reset_rejects_weak_passwords_and_wrong_link_types(anon_client: TestClient) -> None:
    register(anon_client)
    anon_client.post("/api/auth/forgot-password", json={"email": EMAIL})
    token = outbox_of(anon_client).last_token(EMAIL)
    assert anon_client.post("/api/auth/reset-password", json={"token": token, "password": "corta"}).status_code == 422
    verify_link = create_action_token(VERIFY_EMAIL, 1, secret=TEST_JWT_SECRET, minutes=5)
    assert (
        anon_client.post("/api/auth/reset-password", json={"token": verify_link, "password": NEW_PASSWORD}).status_code
        == 400
    )
    assert _login(anon_client, TEST_PASSWORD) == 200  # nada cambió


def test_reset_emails_are_throttled_per_address(anon_client: TestClient) -> None:
    register(anon_client)
    for _ in range(6):
        anon_client.post("/api/auth/forgot-password", json={"email": EMAIL})
    resets = [m for m in outbox_of(anon_client).to(EMAIL) if "Restablece" in m[1]]
    assert len(resets) == 3


# ── Cierre de sesión ─────────────────────────────────────────────────────────────


def test_logout_revokes_every_session_of_the_account(anon_client: TestClient) -> None:
    phone = register(anon_client)
    laptop = {
        "Authorization": f"Bearer {anon_client.post('/api/auth/login', json={'email': EMAIL, 'password': TEST_PASSWORD}).json()['access_token']}"
    }
    assert anon_client.get("/api/auth/me", headers=laptop).status_code == 200

    assert anon_client.post("/api/auth/logout", headers=phone).status_code == 204
    assert anon_client.get("/api/auth/me", headers=phone).status_code == 401
    assert anon_client.get("/api/auth/me", headers=laptop).status_code == 401
    assert _login(anon_client) == 200  # iniciar sesión de nuevo funciona


def test_logout_requires_a_session(anon_client: TestClient) -> None:
    assert anon_client.post("/api/auth/logout").status_code == 401


def test_new_public_account_routes_share_the_strict_auth_rate_limit(make_app: Callable[..., FastAPI]) -> None:
    client = TestClient(make_app(rate_limit_auth_per_minute=2))
    codes = [client.post("/api/auth/forgot-password", json={"email": EMAIL}).status_code for _ in range(4)]
    assert codes == [202, 202, 429, 429]
