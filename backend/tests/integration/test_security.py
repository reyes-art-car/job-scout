from collections.abc import Callable

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.conftest import TEST_JWT_SECRET, register

# ── Autenticación ────────────────────────────────────────────────────────────────

PROD = {
    "app_env": "production",
    "anthropic_api_key": "sk-ant-test",
    "cors_origins": "https://example.com",
    "email_backend": "smtp",
    "smtp_host": "smtp.example.com",
    "email_from": "no-reply@example.com",
    "app_base_url": "https://example.com",
}
PUBLIC = {"/api/health", "/api/auth/register", "/api/auth/login"}


def test_health_is_public_but_offers_require_a_session(anon_client: TestClient) -> None:
    assert anon_client.get("/api/health").status_code == 200
    response = anon_client.get("/api/offers")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("header", ["Bearer wrong", "Bearer ", "Basic abc", "", "bearer"])
def test_invalid_credentials_are_rejected(anon_client: TestClient, header: str) -> None:
    assert anon_client.get("/api/offers", headers={"Authorization": header}).status_code == 401


def test_valid_session_grants_access_to_every_offer_route(client: TestClient) -> None:
    assert client.get("/api/offers").status_code == 200
    assert client.get("/api/offers/stats").status_code == 200
    assert client.get("/api/offers/export.csv").status_code == 200
    assert client.post("/api/offers", json={}).status_code == 422  # autenticada pero inválida


def test_every_non_public_route_is_protected(anon_client: TestClient) -> None:
    """Denegado por defecto: cualquier ruta nueva fuera de la lista pública debe exigir sesión."""
    for route in anon_client.app.routes:  # type: ignore[attr-defined]
        path = getattr(route, "path", "")
        if not path.startswith("/api") or path in PUBLIC:
            continue
        concrete = path.replace("{offer_id}", "1").replace("{job_id}", "1")
        for method in getattr(route, "methods", set()) - {"HEAD", "OPTIONS"}:
            response = anon_client.request(method, concrete)
            assert response.status_code == 401, f"{method} {path} no exige autenticación"


def test_token_signed_with_another_secret_is_rejected(anon_client: TestClient, client: TestClient) -> None:
    from job_tracker.infrastructure.security.tokens import create_access_token

    forged = create_access_token(1, secret="otro-secreto-" + "x" * 30, minutes=5)
    assert anon_client.get("/api/offers", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_expired_token_is_rejected(anon_client: TestClient, client: TestClient) -> None:
    from job_tracker.infrastructure.security.tokens import create_access_token

    expired = create_access_token(1, secret=TEST_JWT_SECRET, minutes=-1)
    assert anon_client.get("/api/offers", headers={"Authorization": f"Bearer {expired}"}).status_code == 401


def test_token_of_a_deleted_user_is_rejected(anon_client: TestClient) -> None:
    from job_tracker.infrastructure.security.tokens import create_access_token

    token = create_access_token(999, secret=TEST_JWT_SECRET, minutes=5)  # ese usuario no existe
    assert anon_client.get("/api/offers", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_unsigned_alg_none_token_is_rejected(anon_client: TestClient, client: TestClient) -> None:
    import base64
    import json

    def part(data: dict) -> str:
        return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()

    forged = f"{part({'alg': 'none', 'typ': 'JWT'})}.{part({'sub': '1', 'exp': 9999999999})}."
    assert anon_client.get("/api/offers", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_register_login_and_me(anon_client: TestClient) -> None:
    headers = register(anon_client, "Ana@Example.com")  # el email se normaliza a minúsculas
    me = anon_client.get("/api/auth/me", headers=headers).json()
    assert me["email"] == "ana@example.com" and me["plan"] == "free"
    assert me["email_verified"] is True  # `register` sigue el enlace del correo, como un usuario real
    assert me["quota"] == {"limit": 1, "used": 0, "remaining": 1}
    login = anon_client.post("/api/auth/login", json={"email": "ANA@example.com", "password": "contraseña-de-prueba-1"})
    assert login.status_code == 200 and login.json()["access_token"]


def test_login_does_not_reveal_which_part_was_wrong(anon_client: TestClient) -> None:
    register(anon_client)
    wrong_password = anon_client.post("/api/auth/login", json={"email": "ana@example.com", "password": "mal"})
    unknown_email = anon_client.post("/api/auth/login", json={"email": "nadie@example.com", "password": "mal"})
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_weak_passwords_and_bad_emails_are_rejected(anon_client: TestClient) -> None:
    short = anon_client.post("/api/auth/register", json={"email": "b@example.com", "password": "corta"})
    assert short.status_code == 422
    bad_email = anon_client.post("/api/auth/register", json={"email": "no-es-email", "password": "x" * 12})
    assert bad_email.status_code == 422


def test_passwords_are_never_stored_or_returned_in_clear(anon_client: TestClient, session) -> None:
    from job_tracker.infrastructure.db.models import UserModel

    response = anon_client.post("/api/auth/register", json={"email": "ana@example.com", "password": "secreto-12345"})
    assert "secreto-12345" not in response.text and "access_token" not in response.text
    stored = session.query(UserModel).one().password_hash
    assert stored.startswith("scrypt$") and "secreto-12345" not in stored


def test_registration_can_be_closed(make_app: Callable[..., FastAPI]) -> None:
    client = TestClient(make_app(registration_open=False))
    response = client.post("/api/auth/register", json={"email": "ana@example.com", "password": "x" * 12})
    assert response.status_code == 403


def test_auth_endpoints_have_a_strict_rate_limit(make_app: Callable[..., FastAPI]) -> None:
    client = TestClient(make_app(rate_limit_auth_per_minute=3))
    codes = [
        client.post("/api/auth/login", json={"email": "a@example.com", "password": "mal"}).status_code for _ in range(5)
    ]
    assert codes == [401, 401, 401, 429, 429]


def test_users_cannot_see_or_touch_each_others_offers(
    make_client: Callable[..., TestClient], offer_payload: dict
) -> None:
    ana = make_client("ana@example.com")
    created = ana.post("/api/offers", json=offer_payload).json()
    bea = TestClient(ana.app, raise_server_exceptions=False)
    bea.headers.update(register(bea, "bea@example.com"))

    assert bea.get("/api/offers").json()["total"] == 0
    assert bea.get(f"/api/offers/{created['id']}").status_code == 404
    assert bea.patch(f"/api/offers/{created['id']}", json={"notes": "mío"}).status_code == 404
    assert bea.patch(f"/api/offers/{created['id']}/status", json={"status": "Aplicado"}).status_code == 404
    assert bea.get("/api/offers/stats").json()["total"] == 0
    # La misma URL y el mismo código OF001 son válidos para otro usuario: la unicidad es por cuenta.
    assert bea.post("/api/offers", json=offer_payload).json()["code"] == "OF001"
    assert ana.get(f"/api/offers/{created['id']}").json()["notes"] is None


# ── Cabeceras y exposición ───────────────────────────────────────────────────────


def test_security_headers_are_present(client: TestClient) -> None:
    headers = client.get("/api/health").headers
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert headers["referrer-policy"] == "no-referrer"
    assert "default-src 'none'" in headers["content-security-policy"]
    assert headers["cache-control"] == "no-store"
    assert "strict-transport-security" not in headers  # solo en producción


def test_hsts_is_sent_in_production(make_app: Callable[..., FastAPI]) -> None:
    app = make_app(**PROD)
    response = TestClient(app).get("/api/health")
    assert "max-age=31536000" in response.headers["strict-transport-security"]


def test_docs_are_hidden_in_production(make_app: Callable[..., FastAPI]) -> None:
    app = make_app(**PROD)
    prod = TestClient(app)
    assert prod.get("/docs").status_code == 404
    assert prod.get("/openapi.json").status_code == 404
    dev = TestClient(make_app())
    assert dev.get("/docs").status_code == 200


def test_unknown_host_header_is_rejected(client: TestClient) -> None:
    assert client.get("/api/health", headers={"Host": "evil.example"}).status_code == 400


def test_cors_only_allows_configured_origins(client: TestClient) -> None:
    allowed = client.get("/api/health", headers={"Origin": "http://localhost:4200"})
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:4200"
    assert "access-control-allow-credentials" not in allowed.headers
    denied = client.get("/api/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in denied.headers


# ── Límites ──────────────────────────────────────────────────────────────────────


def test_rate_limit_returns_429_with_retry_after(make_client: Callable[..., TestClient]) -> None:
    client = make_client(rate_limit_per_minute=3)
    codes = [client.get("/api/offers/stats").status_code for _ in range(5)]
    assert codes == [200, 200, 200, 429, 429]
    blocked = client.get("/api/offers/stats")
    assert int(blocked.headers["retry-after"]) >= 1
    assert client.get("/api/health").status_code == 200  # el health check nunca se limita


def test_write_and_export_have_their_own_stricter_limits(
    make_client: Callable[..., TestClient], offer_payload: dict
) -> None:
    client = make_client(rate_limit_writes_per_minute=2, rate_limit_exports_per_minute=1)
    posts = [
        client.post("/api/offers", json={**offer_payload, "url": f"https://e.com/{i}"}).status_code for i in range(3)
    ]
    assert posts == [201, 201, 429]
    assert [client.get("/api/offers/export.csv").status_code for _ in range(2)] == [200, 429]


def test_oversized_body_is_rejected(make_client: Callable[..., TestClient]) -> None:
    client = make_client(max_body_bytes=200)
    response = client.post("/api/offers", content=b"x" * 500, headers={"Content-Type": "application/json"})
    assert response.status_code == 413


def test_pagination_is_bounded(client: TestClient) -> None:
    assert client.get("/api/offers", params={"page_size": 100_000}).status_code == 422
    assert client.get("/api/offers", params={"page": 0}).status_code == 422
    assert client.get("/api/offers", params={"search": "a" * 101}).status_code == 422
    assert client.get("/api/offers", params={"min_compatibility": 500}).status_code == 422


# ── Validación y saneado de entradas ─────────────────────────────────────────────


def test_html_is_stripped_from_text_fields(client: TestClient, offer_payload: dict) -> None:
    payload = {
        **offer_payload,
        "title": "Dev <script>alert(1)</script>Java",
        "notes": "<img src=x onerror=alert(1)>Hola",
    }
    body = client.post("/api/offers", json=payload).json()
    assert "<" not in body["title"] and "script" not in body["title"].lower().replace("javascript", "")
    assert body["title"] == "Dev Java"
    assert body["notes"] == "Hola"


def test_control_and_bidi_characters_are_removed(client: TestClient, offer_payload: dict) -> None:
    payload = {**offer_payload, "company": "Ac\u202eme\x00\u200b Corp"}
    assert client.post("/api/offers", json=payload).json()["company"] == "Acme Corp"


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "data:text/html,<b>x</b>",
        "file:///etc/passwd",
        "ftp://x.com/a",
        "//evil.com",
        "no es una url",
    ],
)
def test_non_http_urls_are_rejected(client: TestClient, offer_payload: dict, url: str) -> None:
    assert client.post("/api/offers", json={**offer_payload, "url": url}).status_code == 422


def test_unknown_fields_are_rejected_not_ignored(client: TestClient, offer_payload: dict) -> None:
    for extra in ({"id": 99}, {"code": "OF999"}, {"adapted_cv_filename": "../../etc/passwd"}, {"source": "x"}):
        assert client.post("/api/offers", json={**offer_payload, **extra}).status_code == 422


def test_validation_errors_do_not_echo_the_input(client: TestClient, offer_payload: dict) -> None:
    secret = "valor-sensible-12345"
    response = client.post("/api/offers", json={**offer_payload, "compatibility": secret})
    assert response.status_code == 422
    assert secret not in response.text


def test_search_wildcards_are_treated_literally(client: TestClient, offer_payload: dict) -> None:
    client.post("/api/offers", json=offer_payload)
    assert client.get("/api/offers", params={"search": "%"}).json()["total"] == 0
    assert client.get("/api/offers", params={"search": "_"}).json()["total"] == 0
    assert client.get("/api/offers", params={"search": "acme"}).json()["total"] == 1


def test_sql_injection_attempts_are_inert(client: TestClient, offer_payload: dict) -> None:
    client.post("/api/offers", json=offer_payload)
    response = client.get("/api/offers", params={"search": "' OR 1=1 --"})
    assert response.status_code == 200 and response.json()["total"] == 0
    assert client.get("/api/offers/1 OR 1=1").status_code == 422


# ── Errores y ficheros ───────────────────────────────────────────────────────────


def test_unexpected_errors_do_not_leak_internals(make_app: Callable[..., FastAPI]) -> None:
    app = make_app()

    @app.get("/boom")
    def boom() -> None:
        raise RuntimeError("password=hunter2 en /srv/secreto/ruta.py")

    response = TestClient(app, raise_server_exceptions=False).get("/boom")
    assert response.status_code == 500
    assert "hunter2" not in response.text and "secreto" not in response.text
    assert response.json()["incident"]
    assert response.headers["x-content-type-options"] == "nosniff"  # también los 500 llevan cabeceras de seguridad


def test_cv_download_is_confined_to_the_cv_directory(
    make_client: Callable[..., TestClient], session, tmp_path, offer_payload: dict
) -> None:
    from job_tracker.domain.offer.entities import KanbanStatus, Offer, OfferSource, Priority
    from job_tracker.infrastructure.db.sqlalchemy_offer_repository import SqlAlchemyOfferRepository

    cvs = tmp_path / "cvs"
    cvs.mkdir()
    (cvs / "ok.docx").write_bytes(b"cv")
    (tmp_path / "secreto.txt").write_text("no debe salir")

    client = make_client()
    repo = SqlAlchemyOfferRepository(session, 1)  # el primer usuario registrado
    for i, filename in enumerate(["ok.docx", "../secreto.txt", "..\\secreto.txt", "/etc/passwd"]):
        repo.add(
            Offer(
                id=None,
                code=f"OF{i + 1:03d}",
                priority=Priority.ALTA,
                compatibility=80,
                title="t",
                company="c",
                portal="p",
                url=f"https://e.com/{i}",
                published_date=None,
                location="",
                modality="",
                contract_type="",
                salary=None,
                experience_required="",
                mandatory_tech="",
                desirable_tech="",
                requirements_met="",
                requirements_missing="",
                score_reason="",
                kanban_status=KanbanStatus.PENDIENTE,
                adapted_cv_filename=filename,
                notes=None,
                source=OfferSource.LEGACY_EXCEL,
            )
        )

    assert client.get("/api/offers/1/cv").content == b"cv"
    for offer_id in (2, 3, 4):
        response = client.get(f"/api/offers/{offer_id}/cv")
        assert response.status_code in (200, 404)
        assert b"no debe salir" not in response.content


# ── Fuerza bruta y abuso ─────────────────────────────────────────────────────────


def test_account_is_locked_after_repeated_failed_logins(make_app: Callable[..., FastAPI]) -> None:
    client = TestClient(make_app(login_failures_per_window=3))
    register(client)
    wrong = {"email": "ana@example.com", "password": "mal"}
    assert [client.post("/api/auth/login", json=wrong).status_code for _ in range(3)] == [401, 401, 401]
    blocked = client.post("/api/auth/login", json=wrong)
    assert blocked.status_code == 429 and int(blocked.headers["retry-after"]) >= 1
    # Bloqueada de verdad: ni siquiera la contraseña correcta entra mientras dura el bloqueo.
    correct = {"email": "ana@example.com", "password": "contraseña-de-prueba-1"}
    assert client.post("/api/auth/login", json=correct).status_code == 429
    # Otra cuenta no se ve afectada.
    assert client.post("/api/auth/login", json={"email": "otra@example.com", "password": "mal"}).status_code == 401


def test_successful_login_resets_the_failure_counter(make_app: Callable[..., FastAPI]) -> None:
    client = TestClient(make_app(login_failures_per_window=3))
    register(client)
    wrong = {"email": "ana@example.com", "password": "mal"}
    correct = {"email": "ana@example.com", "password": "contraseña-de-prueba-1"}
    for _ in range(2):
        client.post("/api/auth/login", json=wrong)
    assert client.post("/api/auth/login", json=correct).status_code == 200
    assert [client.post("/api/auth/login", json=wrong).status_code for _ in range(2)] == [401, 401]


def test_login_lockout_is_case_insensitive_on_the_email(make_app: Callable[..., FastAPI]) -> None:
    client = TestClient(make_app(login_failures_per_window=2))
    register(client)
    for email in ("ana@example.com", "ANA@example.com"):
        client.post("/api/auth/login", json={"email": email, "password": "mal"})
    assert client.post("/api/auth/login", json={"email": "Ana@Example.com", "password": "mal"}).status_code == 429


def test_csv_neutralizes_every_formula_prefix(client: TestClient, offer_payload: dict) -> None:
    for i, prefix in enumerate(["=", "+", "-", "@", "\t", "\r"]):
        client.post(
            "/api/offers", json={**offer_payload, "url": f"https://e.com/{i}", "notes": f"{prefix}cmd|' /C calc'!A0"}
        )
    csv_text = client.get("/api/offers/export.csv").text
    assert all(f'"{prefix}cmd' not in csv_text for prefix in ["=", "+", "-", "@", "\t", "\r"])


def test_an_attacker_cannot_lock_the_real_owner_out_from_another_ip(make_app: Callable[..., FastAPI]) -> None:
    client = TestClient(make_app(login_failures_per_window=3, trust_proxy=True))
    register(client)
    wrong = {"email": "ana@example.com", "password": "mal"}
    attacker = {"X-Forwarded-For": "203.0.113.50"}
    owner = {"X-Forwarded-For": "198.51.100.7"}
    for _ in range(3):
        client.post("/api/auth/login", json=wrong, headers=attacker)
    assert client.post("/api/auth/login", json=wrong, headers=attacker).status_code == 429  # el atacante, bloqueado
    correct = {"email": "ana@example.com", "password": "contraseña-de-prueba-1"}
    assert client.post("/api/auth/login", json=correct, headers=owner).status_code == 200  # la dueña, no


def test_a_distributed_attack_on_one_account_is_still_stopped(make_app: Callable[..., FastAPI]) -> None:
    client = TestClient(make_app(login_failures_per_window=2, trust_proxy=True))
    register(client)
    wrong = {"email": "ana@example.com", "password": "mal"}
    # Tope por cuenta = 2 x 5 = 10 fallos repartidos entre IPs distintas (ninguna llega a su propio tope).
    for i in range(10):
        client.post("/api/auth/login", json=wrong, headers={"X-Forwarded-For": f"203.0.113.{i}"})
    assert client.post("/api/auth/login", json=wrong, headers={"X-Forwarded-For": "203.0.113.200"}).status_code == 429
