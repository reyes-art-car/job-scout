from datetime import datetime

from pydantic import BaseModel, ConfigDict

from job_tracker.domain.search.entities import SearchJob, SearchStatus


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy: str = "general"


class SearchJobOut(BaseModel):
    id: int
    strategy: str
    status: SearchStatus
    created_at: datetime | None
    started_at: datetime | None
    finished_at: datetime | None
    offers_added: int
    offers_skipped: int
    error: str | None

    @classmethod
    def from_entity(cls, job: SearchJob) -> "SearchJobOut":
        # No se expone el consumo de tokens al usuario: es un dato interno de coste.
        return cls.model_validate(job, from_attributes=True)
