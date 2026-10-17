from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from job_tracker.api.schemas.types import SafeUrl, Text100, Text255, Text4000
from job_tracker.domain.offer.entities import KanbanStatus, Offer, OfferSource, Priority


class OfferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
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
    created_at: datetime | None
    updated_at: datetime | None

    @classmethod
    def from_entity(cls, offer: Offer) -> "OfferOut":
        return cls.model_validate(offer, from_attributes=True)


class OfferListOut(BaseModel):
    items: list[OfferOut]
    total: int
    page: int
    page_size: int


class OfferStatsOut(BaseModel):
    total: int
    high_priority: int
    by_status: dict[str, int]


class OfferStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: KanbanStatus


class OfferPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    notes: Text4000 | None = None
    salary: Text255 | None = None
    kanban_status: KanbanStatus | None = None


class OfferCreate(BaseModel):
    # extra="forbid": un campo desconocido es un error, no se ignora en silencio (evita mass assignment).
    model_config = ConfigDict(extra="forbid")

    title: Text255 = Field(min_length=1)
    company: Text255 = Field(min_length=1)
    portal: Text255 = "Otro"
    url: SafeUrl | None = None
    published_date: date | None = None
    location: Text255 = ""
    modality: Text100 = ""
    contract_type: Text100 = "No especificado"
    salary: Text255 | None = None
    experience_required: Text255 = "No especificado"
    mandatory_tech: Text4000 = ""
    desirable_tech: Text4000 = ""
    requirements_met: Text4000 = ""
    requirements_missing: Text4000 = ""
    score_reason: Text4000 = ""
    compatibility: int = Field(default=0, ge=0, le=100)
    kanban_status: KanbanStatus = KanbanStatus.PENDIENTE
    notes: Text4000 | None = None
    priority: Priority | None = None
