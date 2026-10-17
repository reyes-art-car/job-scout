from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

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
    status: KanbanStatus


class OfferPatch(BaseModel):
    notes: str | None = None
    salary: str | None = None
    kanban_status: KanbanStatus | None = None


class OfferCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    company: str = Field(min_length=1, max_length=255)
    portal: str = Field(default="Otro", max_length=255)
    url: str | None = Field(default=None, max_length=1000)
    published_date: date | None = None
    location: str = Field(default="", max_length=255)
    modality: str = Field(default="", max_length=100)
    contract_type: str = Field(default="No especificado", max_length=100)
    salary: str | None = Field(default=None, max_length=255)
    experience_required: str = Field(default="No especificado", max_length=255)
    mandatory_tech: str = ""
    desirable_tech: str = ""
    requirements_met: str = ""
    requirements_missing: str = ""
    score_reason: str = ""
    compatibility: int = Field(default=0, ge=0, le=100)
    kanban_status: KanbanStatus = KanbanStatus.PENDIENTE
    notes: str | None = None
    priority: Priority | None = None
