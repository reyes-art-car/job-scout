from datetime import datetime
from typing import Protocol

from job_tracker.domain.search.entities import SearchJob


class SearchJobReader(Protocol):
    """Lo que ve un usuario: siempre acotado a su propio `user_id`."""

    def get(self, user_id: int, job_id: int) -> SearchJob | None: ...

    def list_for_user(self, user_id: int, limit: int) -> list[SearchJob]: ...

    def count_quota_used_since(self, user_id: int, since: datetime) -> int: ...

    def has_active(self, user_id: int) -> bool: ...


class SearchJobQueue(Protocol):
    """Lo que ve el worker: cola global."""

    def add(self, job: SearchJob) -> SearchJob: ...

    def claim_next(self) -> SearchJob | None:
        """Pasa el trabajo en cola más antiguo a «en curso» y lo devuelve (None si no hay)."""
        ...

    def save(self, job: SearchJob) -> SearchJob: ...

    def fail_stale(self, older_than: datetime) -> int:
        """Marca como fallidos los trabajos «en curso» iniciados antes de `older_than`. Devuelve cuántos."""
        ...
