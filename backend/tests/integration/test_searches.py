import json
from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from job_tracker.domain.search.entities import SearchStatus
from job_tracker.domain.search.exceptions import LlmError
from job_tracker.domain.search.llm import LlmResult
from job_tracker.infrastructure.db.models import SearchJobModel, UserModel
from job_tracker.worker import process_next

PROFILE = {
    "headline": "Desarrolladora Java junior",
    "seniority": "junior",
    "summary": "CFGS DAW. Prácticas con Spring Boot y Angular.",
    "skills": ["Java", "Spring Boot", "Angular"],
    "target_roles": ["Backend Java", "Full stack"],
    "onsite_cities": ["Sevilla"],
}


def _offer(**overrides: object) -> dict:
    return {
        "compatibility": 82,
        "title": "Java Developer Junior",
        "company": "Acme",
        "portal": "LinkedIn",
        "url": "https://example.com/jobs/1",
        "date": "2026-10-18",
        "location": "Sevilla",
        "modality": "Híbrido",
        "mandatory_tech": "Java, Spring Boot",
        **overrides,
    }


class FakeLlm:
    def __init__(self, offers: list[dict] | None = None, error: str | None = None) -> None:
        self.offers = offers if offers is not None else [_offer()]
        self.error = error
        self.prompts: list[str] = []

    def search(self, prompt: str) -> LlmResult:
        self.prompts.append(prompt)
        if self.error:
            raise LlmError(self.error)
        return LlmResult(
            "Aquí tienes:\n```json\n" + json.dumps(self.offers) + "\n```",
            input_tokens=1200,
            output_tokens=300,
            web_searches=4,
            web_fetches=2,
        )


def _set_plan(session: Session, plan: str) -> None:
    session.query(UserModel).update({"plan": plan})
    session.commit()


# ── Perfil ───────────────────────────────────────────────────────────────────────


def test_profile_is_null_until_saved_then_round_trips(client: TestClient) -> None:
    assert client.get("/api/profile").json() is None
    saved = client.put("/api/profile", json=PROFILE)
    assert saved.status_code == 200
    assert client.get("/api/profile").json()["skills"] == ["Java", "Spring Boot", "Angular"]


def test_profile_text_is_sanitized_and_bounded(client: TestClient) -> None:
    saved = client.put("/api/profile", json={**PROFILE, "headline": "Dev <script>x</script>Java"})
    assert saved.json()["headline"] == "Dev Java"
    assert client.put("/api/profile", json={**PROFILE, "skills": ["x"] * 21}).status_code == 422
    assert client.put("/api/profile", json={**PROFILE, "summary": "corto"}).status_code == 422
    assert client.put("/api/profile", json={**PROFILE, "es_admin": True}).status_code == 422


def test_profiles_are_private_to_each_user(make_client: Callable[..., TestClient]) -> None:
    ana = make_client("ana@example.com")
    ana.put("/api/profile", json=PROFILE)
    bea = TestClient(ana.app)
    from tests.conftest import register

    bea.headers.update(register(bea, "bea@example.com"))
    assert bea.get("/api/profile").json() is None


# ── Encolar ──────────────────────────────────────────────────────────────────────


def test_search_requires_a_profile(client: TestClient) -> None:
    response = client.post("/api/searches", json={"strategy": "general"})
    assert response.status_code == 409


def test_search_is_queued_and_listed(client: TestClient) -> None:
    client.put("/api/profile", json=PROFILE)
    created = client.post("/api/searches", json={"strategy": "linkedin"})
    assert created.status_code == 202
    assert created.json()["status"] == "queued"
    job_id = created.json()["id"]
    assert client.get(f"/api/searches/{job_id}").json()["strategy"] == "linkedin"
    assert [job["id"] for job in client.get("/api/searches").json()] == [job_id]


def test_unknown_strategy_is_rejected(client: TestClient) -> None:
    client.put("/api/profile", json=PROFILE)
    assert client.post("/api/searches", json={"strategy": "hackear"}).status_code == 422


def test_only_one_search_at_a_time(client: TestClient, session: Session) -> None:
    _set_plan(session, "pro")
    client.put("/api/profile", json=PROFILE)
    assert client.post("/api/searches", json={}).status_code == 202
    assert client.post("/api/searches", json={}).status_code == 409


def test_free_plan_quota_is_enforced_and_pro_has_more(client: TestClient, session: Session) -> None:
    client.put("/api/profile", json=PROFILE)
    first = client.post("/api/searches", json={}).json()["id"]
    session.query(SearchJobModel).update({"status": "done"})
    session.commit()
    blocked = client.post("/api/searches", json={})
    assert blocked.status_code == 402 and blocked.json()["limit"] == 1
    assert client.get("/api/auth/me").json()["quota"] == {"limit": 1, "used": 1, "remaining": 0}

    _set_plan(session, "pro")
    assert client.post("/api/searches", json={}).status_code == 202
    assert first != client.get("/api/searches").json()[0]["id"]


def test_failed_searches_do_not_consume_quota(client: TestClient, session: Session) -> None:
    client.put("/api/profile", json=PROFILE)
    client.post("/api/searches", json={})
    session.query(SearchJobModel).update({"status": "failed"})
    session.commit()
    assert client.post("/api/searches", json={}).status_code == 202


def test_a_user_cannot_read_another_users_search(make_client: Callable[..., TestClient]) -> None:
    from tests.conftest import register

    ana = make_client("ana@example.com")
    ana.put("/api/profile", json=PROFILE)
    job_id = ana.post("/api/searches", json={}).json()["id"]
    bea = TestClient(ana.app)
    bea.headers.update(register(bea, "bea@example.com"))
    assert bea.get(f"/api/searches/{job_id}").status_code == 404
    assert bea.get("/api/searches").json() == []


def test_job_output_hides_internal_cost_data(client: TestClient) -> None:
    client.put("/api/profile", json=PROFILE)
    body = client.post("/api/searches", json={}).json()
    assert "input_tokens" not in body and "output_tokens" not in body


# ── Worker ───────────────────────────────────────────────────────────────────────


def test_worker_runs_the_job_and_saves_offers_for_that_user(client: TestClient, session: Session) -> None:
    client.put("/api/profile", json=PROFILE)
    job_id = client.post("/api/searches", json={}).json()["id"]
    llm = FakeLlm([_offer(), _offer(url="https://example.com/jobs/2", title="Backend Java")])

    assert process_next(session, llm) is True
    assert process_next(session, llm) is False  # cola vacía

    job = client.get(f"/api/searches/{job_id}").json()
    assert job["status"] == "done" and job["offers_added"] == 2
    offers = client.get("/api/offers").json()
    assert offers["total"] == 2 and offers["items"][0]["source"] == "claude_agent_search"
    row = session.get(SearchJobModel, job_id)
    assert (row.input_tokens, row.output_tokens, row.web_searches, row.web_fetches) == (1200, 300, 4, 2)  # type: ignore[union-attr]
    assert "Desarrolladora Java junior" in llm.prompts[0]


def test_worker_does_not_repeat_known_urls_nor_save_invalid_offers(client: TestClient, session: Session) -> None:
    client.put("/api/profile", json=PROFILE)
    client.post("/api/offers", json={"title": "Ya la tenía", "company": "X", "url": "https://example.com/jobs/1"})
    client.post("/api/searches", json={})
    llm = FakeLlm(
        [
            _offer(),  # URL ya guardada
            _offer(url="javascript:alert(1)"),  # URL peligrosa
            _offer(url="https://example.com/jobs/3", compatibility=40),  # por debajo del mínimo
            _offer(url="https://example.com/jobs/4", title="<b>Válida</b>"),
        ]
    )
    process_next(session, llm)
    assert "https://example.com/jobs/1" in llm.prompts[0]  # se le dice al modelo qué URLs ya existen
    job = client.get("/api/searches").json()[0]
    assert (job["offers_added"], job["offers_skipped"]) == (1, 3)
    assert {o["title"] for o in client.get("/api/offers").json()["items"]} == {"Ya la tenía", "Válida"}


def test_worker_failure_is_recorded_without_leaking_details(client: TestClient, session: Session) -> None:
    client.put("/api/profile", json=PROFILE)
    client.post("/api/searches", json={})
    process_next(session, FakeLlm(error="El servicio de búsqueda no está disponible ahora mismo"))
    job = client.get("/api/searches").json()[0]
    assert job["status"] == SearchStatus.FAILED.value
    assert job["error"] == "El servicio de búsqueda no está disponible ahora mismo"


def test_unexpected_worker_errors_are_generic(client: TestClient, session: Session) -> None:
    class Exploding:
        def search(self, _prompt: str) -> LlmResult:
            raise RuntimeError("sk-ant-secreto en /srv/ruta")

    client.put("/api/profile", json=PROFILE)
    client.post("/api/searches", json={})
    process_next(session, Exploding())
    job = client.get("/api/searches").json()[0]
    assert job["status"] == "failed" and "secreto" not in job["error"]


def test_stale_running_jobs_are_failed(session: Session, client: TestClient) -> None:
    from datetime import timedelta

    from job_tracker.application.search.start_search import utc_now
    from job_tracker.infrastructure.db.sqlalchemy_search_job_repository import SqlAlchemySearchJobRepository

    client.put("/api/profile", json=PROFILE)
    job_id = client.post("/api/searches", json={}).json()["id"]
    session.query(SearchJobModel).update({"status": "running", "started_at": utc_now() - timedelta(hours=2)})
    session.commit()
    assert SqlAlchemySearchJobRepository(session).fail_stale(utc_now() - timedelta(minutes=30)) == 1
    assert client.get(f"/api/searches/{job_id}").json()["status"] == "failed"


@pytest.mark.parametrize("strategy", ["general", "linkedin", "europa"])
def test_every_strategy_produces_a_prompt(client: TestClient, session: Session, strategy: str) -> None:
    client.put("/api/profile", json=PROFILE)
    client.post("/api/searches", json={"strategy": strategy})
    llm = FakeLlm([])
    process_next(session, llm)
    assert "<perfil_candidato>" in llm.prompts[0] and "NO confiable" in llm.prompts[0]


def test_global_daily_budget_stops_new_searches_for_everyone(make_client: Callable[..., TestClient]) -> None:
    from tests.conftest import register

    ana = make_client("ana@example.com", max_searches_per_day=1)
    ana.put("/api/profile", json=PROFILE)
    assert ana.post("/api/searches", json={}).status_code == 202

    bea = TestClient(ana.app)
    bea.headers.update(register(bea, "bea@example.com"))
    bea.put("/api/profile", json=PROFILE)
    blocked = bea.post("/api/searches", json={})
    assert blocked.status_code == 503  # tope global: no importa que Bea no haya gastado su cupo
