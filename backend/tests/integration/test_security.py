from collections.abc import Callable

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.conftest import TEST_TOKEN

AUTH = {"Authorization": f"Bearer {TEST_TOKEN}"}


# ── Autenticación ────────────────────────────────────────────────────────────────


def test_health_is_public_but_offers_require_token(secured_client: TestClient) -> None:
    assert secured_client.get("/api/health").status_code == 200
    response = secured_client.get("/api/offers")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_access_check_only_accepts_the_right_key(secured_client: TestClient) -> None:
    assert secured_client.get("/api/auth/check").status_code == 401
    assert secured_client.get("/api/auth/check", headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert secured_client.get("/api/auth/check", headers=AUTH).status_code == 204


@pytest.mark.parametrize("header", ["Bearer wrong", "Bearer ", "Basic abc", "", f"bearer{TEST_TOKEN}"])
def test_invalid_credentials_are_rejected(secured_client: TestClient, header: str) -> None:
    assert secured_client.get("/api/offers", headers={"Authorization": header}).status_code == 401


def test_valid_token_grants_access_to_every_offer_route(secured_client: TestClient) -> None:
    assert secured_client.get("/api/offers", headers=AUTH).status_code == 200
    assert secured_client.get("/api/offers/stats", headers=AUTH).status_code == 200
    assert secured_client.get("/api/offers/export.csv", headers=AUTH).status_code == 200
    assert secured_client.post("/api/offers", json={}, headers=AUTH).status_code == 422  # autenticada pero inválida


def test_every_non_public_route_is_protected(secured_client: TestClient) -> None:
    """Denegado por defecto: cualquier ruta nueva fuera de la lista pública debe exigir token."""
    public = {"/api/health"}
    for route in secured_client.app.routes:  # type: ignore[attr-defined]
        path = getattr(route, "path", "")
        if not path.startswith("/api") or path in public:
            continue
        concrete = path.replace("{offer_id}", "1")
        for method in getattr(route, "methods", set()) - {"HEAD", "OPTIONS"}:
            response = secured_client.request(method, concrete)
            assert response.status_code == 401, f"{method} {path} no exige autenticación"


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
    app = make_app(app_env="production", api_token=TEST_TOKEN, cors_origins="https://example.com")
    response = TestClient(app).get("/api/health")
    assert "max-age=31536000" in response.headers["strict-transport-security"]


def test_docs_are_hidden_in_production(make_app: Callable[..., FastAPI]) -> None:
    app = make_app(app_env="production", api_token=TEST_TOKEN, cors_origins="https://example.com")
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


def test_rate_limit_returns_429_with_retry_after(make_app: Callable[..., FastAPI]) -> None:
    client = TestClient(make_app(rate_limit_per_minute=3))
    codes = [client.get("/api/offers/stats").status_code for _ in range(5)]
    assert codes == [200, 200, 200, 429, 429]
    blocked = client.get("/api/offers/stats")
    assert int(blocked.headers["retry-after"]) >= 1
    assert client.get("/api/health").status_code == 200  # el health check nunca se limita


def test_write_and_export_have_their_own_stricter_limits(make_app: Callable[..., FastAPI], offer_payload: dict) -> None:
    client = TestClient(make_app(rate_limit_writes_per_minute=2, rate_limit_exports_per_minute=1))
    posts = [
        client.post("/api/offers", json={**offer_payload, "url": f"https://e.com/{i}"}).status_code for i in range(3)
    ]
    assert posts == [201, 201, 429]
    assert [client.get("/api/offers/export.csv").status_code for _ in range(2)] == [200, 429]


def test_oversized_body_is_rejected(make_app: Callable[..., FastAPI]) -> None:
    client = TestClient(make_app(max_body_bytes=200))
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
    make_app: Callable[..., FastAPI], session, tmp_path, offer_payload: dict
) -> None:
    from job_tracker.domain.offer.entities import KanbanStatus, Offer, OfferSource, Priority
    from job_tracker.infrastructure.db.sqlalchemy_offer_repository import SqlAlchemyOfferRepository

    cvs = tmp_path / "cvs"
    cvs.mkdir()
    (cvs / "ok.docx").write_bytes(b"cv")
    (tmp_path / "secreto.txt").write_text("no debe salir")

    repo = SqlAlchemyOfferRepository(session)
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

    client = TestClient(make_app(), raise_server_exceptions=False)
    assert client.get("/api/offers/1/cv").content == b"cv"
    for offer_id in (2, 3, 4):
        response = client.get(f"/api/offers/{offer_id}/cv")
        assert response.status_code in (200, 404)
        assert b"no debe salir" not in response.content
