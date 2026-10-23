from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class SearchStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


ACTIVE_STATUSES = (SearchStatus.QUEUED, SearchStatus.RUNNING)
# Las búsquedas fallidas no gastan cupo: el fallo no es culpa del usuario.
QUOTA_STATUSES = (SearchStatus.QUEUED, SearchStatus.RUNNING, SearchStatus.DONE)


@dataclass
class SearchJob:
    id: int | None
    user_id: int
    strategy: str
    status: SearchStatus = SearchStatus.QUEUED
    created_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    offers_added: int = 0
    offers_skipped: int = 0
    error: str | None = None
    # Consumo real de la API: base para fijar el precio del plan con datos y no con estimaciones.
    input_tokens: int = 0
    output_tokens: int = 0
    web_searches: int = 0
    web_fetches: int = 0
