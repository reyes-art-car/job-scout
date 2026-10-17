from datetime import date
from pathlib import Path

import openpyxl
import pytest

from job_tracker.domain.offer.entities import KanbanStatus, OfferSource, Priority
from job_tracker.infrastructure.db.sqlalchemy_offer_repository import SqlAlchemyOfferRepository
from job_tracker.infrastructure.excel_import.importer import import_demo_json, import_excel

REPO_ROOT = Path(__file__).resolve().parents[4]
HEADERS = [
    "ID",
    "Prioridad",
    "% Compatibilidad",
    "Puesto",
    "Empresa",
    "Portal",
    "Enlace",
    "Fecha publicación",
    "Ubicación",
    "Modalidad",
    "Tipo contrato",
    "Salario",
    "Experiencia solicitada",
    "Tecnologías obligatorias",
    "Tecnologías deseables",
    "Requisitos que cumplo",
    "Requisitos que NO cumplo",
    "Motivo puntuación",
    "Estado candidatura",
    "Nombre CV adaptado",
    "Observaciones",
]


def _row(code: str, url: str, status: str = "Pendiente de revisión") -> list:
    return [
        code,
        "Alta",
        "82%",
        "Java Developer",
        "Acme",
        "Tecnoempleo",
        url,
        "2026-09-03",
        "España",
        "Remoto 100%",
        "Indefinido",
        "30.000 €",
        "1-2 años",
        "Java, Spring Boot",
        "Docker",
        "Java ✓",
        "Kafka",
        "Tech 30/40",
        status,
        "OF001_Acme.docx",
        "Nota",
    ]


@pytest.fixture
def excel_file(tmp_path: Path) -> Path:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(HEADERS)
    sheet.append(_row("OF001", "https://example.com/1"))
    sheet.append(_row("OF002", "https://example.com/2", status="Entrevista programada"))
    sheet.append(_row("OF001", "https://example.com/dup"))  # mismo ID: duplicada
    sheet.append(["", None, None, None, None])  # fila vacía: inválida
    path = tmp_path / "ofertas.xlsx"
    workbook.save(path)
    return path


def test_import_excel_maps_columns_and_skips_duplicates(
    excel_file: Path, repository: SqlAlchemyOfferRepository
) -> None:
    report = import_excel(excel_file, repository)

    assert (report.imported, report.skipped_duplicates, report.skipped_invalid) == (2, 1, 1)
    first = repository.get_by_code("OF001")
    assert first is not None
    assert first.compatibility == 82
    assert first.priority is Priority.ALTA
    assert first.published_date == date(2026, 9, 3)
    assert first.kanban_status is KanbanStatus.PENDIENTE
    assert first.source is OfferSource.LEGACY_EXCEL
    second = repository.get_by_code("OF002")
    assert second is not None and second.kanban_status is KanbanStatus.ENTREVISTA


def test_import_excel_is_idempotent(excel_file: Path, repository: SqlAlchemyOfferRepository) -> None:
    import_excel(excel_file, repository)
    again = import_excel(excel_file, repository)
    assert again.imported == 0
    assert again.skipped_duplicates == 3


def test_import_demo_json_loads_every_offer(repository: SqlAlchemyOfferRepository) -> None:
    report = import_demo_json(REPO_ROOT / "data" / "demo" / "offers.json", repository)
    assert report.imported >= 10
    assert report.skipped_duplicates == 0
    assert repository.next_code() > "OF130"
