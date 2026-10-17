from fastapi.testclient import TestClient


def _create(client: TestClient, payload: dict) -> dict:
    response = client.post("/api/offers", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_health(client: TestClient) -> None:
    assert client.get("/api/health").json() == {"status": "ok"}


def test_create_assigns_sequential_code_and_priority(client: TestClient, offer_payload: dict) -> None:
    first = _create(client, offer_payload)
    second = _create(client, {**offer_payload, "url": "https://example.com/oferta-2", "compatibility": 60})

    assert first["code"] == "OF001"
    assert first["priority"] == "Alta"
    assert second["code"] == "OF002"
    assert second["priority"] == "Secundaria"
    assert first["kanban_status"] == "Pendiente"


def test_create_rejects_duplicate_url(client: TestClient, offer_payload: dict) -> None:
    _create(client, offer_payload)
    response = client.post("/api/offers", json=offer_payload)
    assert response.status_code == 409


def test_create_validates_payload(client: TestClient, offer_payload: dict) -> None:
    response = client.post("/api/offers", json={**offer_payload, "compatibility": 150})
    assert response.status_code == 422
    response = client.post("/api/offers", json={**offer_payload, "title": ""})
    assert response.status_code == 422


def test_list_filters_and_orders_by_compatibility(client: TestClient, offer_payload: dict) -> None:
    _create(client, {**offer_payload, "compatibility": 70})
    _create(client, {**offer_payload, "url": "https://example.com/b", "company": "Beta", "compatibility": 90})

    body = client.get("/api/offers").json()
    assert body["total"] == 2
    assert [o["compatibility"] for o in body["items"]] == [90, 70]

    assert client.get("/api/offers", params={"min_compatibility": 80}).json()["total"] == 1
    assert client.get("/api/offers", params={"search": "beta"}).json()["total"] == 1
    assert client.get("/api/offers", params={"priority": "Alta"}).json()["total"] == 1


def test_update_status_and_stats(client: TestClient, offer_payload: dict) -> None:
    offer = _create(client, offer_payload)

    response = client.patch(f"/api/offers/{offer['id']}/status", json={"status": "Entrevista"})
    assert response.status_code == 200
    assert response.json()["kanban_status"] == "Entrevista"

    stats = client.get("/api/offers/stats").json()
    assert stats["total"] == 1
    assert stats["high_priority"] == 1
    assert stats["by_status"] == {"Entrevista": 1}


def test_status_rejects_unknown_value(client: TestClient, offer_payload: dict) -> None:
    offer = _create(client, offer_payload)
    response = client.patch(f"/api/offers/{offer['id']}/status", json={"status": "Contratada"})
    assert response.status_code == 422


def test_get_unknown_offer_returns_404(client: TestClient) -> None:
    assert client.get("/api/offers/999").status_code == 404
    assert client.patch("/api/offers/999/status", json={"status": "Aplicado"}).status_code == 404


def test_patch_updates_notes_and_salary(client: TestClient, offer_payload: dict) -> None:
    offer = _create(client, offer_payload)
    response = client.patch(f"/api/offers/{offer['id']}", json={"notes": "Llamar el lunes", "salary": "30.000 €"})
    assert response.json()["notes"] == "Llamar el lunes"
    assert response.json()["salary"] == "30.000 €"


def test_export_csv_is_excel_friendly(client: TestClient, offer_payload: dict) -> None:
    _create(client, {**offer_payload, "notes": "=HYPERLINK(\"http://evil\")"})
    response = client.get("/api/offers/export.csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    text = response.content.decode("utf-8")
    assert text.startswith("﻿")
    header, row = text.removeprefix("﻿").strip().split("\r\n")
    assert header.startswith('"ID";"Prioridad"')
    assert "'=HYPERLINK" in row  # fórmula neutralizada


def test_cv_download_without_adapted_file_returns_404(client: TestClient, offer_payload: dict) -> None:
    offer = _create(client, offer_payload)
    assert client.get(f"/api/offers/{offer['id']}/cv").status_code == 404
