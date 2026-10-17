from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum


class Priority(StrEnum):
    ALTA = "Alta"
    SECUNDARIA = "Secundaria"


class KanbanStatus(StrEnum):
    PENDIENTE = "Pendiente"
    APLICADO = "Aplicado"
    ENTREVISTA = "Entrevista"
    OFERTA = "Oferta"
    RECHAZO = "Rechazo"


class OfferSource(StrEnum):
    LEGACY_EXCEL = "legacy_excel"
    CLAUDE_AGENT_SEARCH = "claude_agent_search"
    DOCUMENT_UPLOAD = "document_upload"


@dataclass
class Offer:
    """Entidad de dominio pura: sin dependencias de SQLAlchemy ni Pydantic."""

    id: int | None
    code: str
    priority: Priority
    compatibility: int
    title: str
    company: str
    portal: str
    url: str | None
    published_date: date | None
    location: str
    modality: str
    contract_type: str
    salary: str | None
    experience_required: str
    mandatory_tech: str
    desirable_tech: str
    requirements_met: str
    requirements_missing: str
    score_reason: str
    kanban_status: KanbanStatus
    adapted_cv_filename: str | None
    notes: str | None
    source: OfferSource
    source_document_filename: str | None = None
    raw_extracted_text: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    extra_bullets_order: list[int] = field(default_factory=list)
    skills_order: str = "backend_first"
    cv_title: str | None = None
    cv_summary: str | None = None
