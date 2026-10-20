from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import CursorResult, Result, func, select, update
from sqlalchemy.orm import Session

from job_tracker.domain.search.entities import ACTIVE_STATUSES, QUOTA_STATUSES, SearchJob, SearchStatus
from job_tracker.infrastructure.db.models import SearchJobModel


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _rowcount(result: Result[Any]) -> int:
    """Filas afectadas por un UPDATE (`Result` no lo declara, `CursorResult` sí)."""
    return cast("CursorResult[Any]", result).rowcount or 0


def _to_entity(row: SearchJobModel) -> SearchJob:
    return SearchJob(
        id=row.id,
        user_id=row.user_id,
        strategy=row.strategy,
        status=SearchStatus(row.status),
        created_at=row.created_at,
        started_at=row.started_at,
        finished_at=row.finished_at,
        offers_added=row.offers_added,
        offers_skipped=row.offers_skipped,
        error=row.error,
        input_tokens=row.input_tokens,
        output_tokens=row.output_tokens,
        web_searches=row.web_searches,
        web_fetches=row.web_fetches,
    )


def _apply(job: SearchJob, row: SearchJobModel) -> None:
    row.strategy = job.strategy
    row.status = job.status.value
    row.started_at = job.started_at
    row.finished_at = job.finished_at
    row.offers_added = job.offers_added
    row.offers_skipped = job.offers_skipped
    row.error = job.error
    row.input_tokens = job.input_tokens
    row.output_tokens = job.output_tokens
    row.web_searches = job.web_searches
    row.web_fetches = job.web_fetches


class SqlAlchemySearchJobRepository:
    """Implementa a la vez la lectura por usuario y la cola global del worker."""

    def __init__(self, session: Session):
        self._session = session

    # --- lectura acotada a un usuario ---
    def get(self, user_id: int, job_id: int) -> SearchJob | None:
        row = self._session.scalar(
            select(SearchJobModel).where(SearchJobModel.id == job_id, SearchJobModel.user_id == user_id)
        )
        return _to_entity(row) if row else None

    def list_for_user(self, user_id: int, limit: int) -> list[SearchJob]:
        stmt = (
            select(SearchJobModel)
            .where(SearchJobModel.user_id == user_id)
            .order_by(SearchJobModel.id.desc())
            .limit(limit)
        )
        return [_to_entity(r) for r in self._session.scalars(stmt)]

    def count_quota_used_since(self, user_id: int, since: datetime) -> int:
        stmt = select(func.count()).where(
            SearchJobModel.user_id == user_id,
            SearchJobModel.created_at >= since,
            SearchJobModel.status.in_([s.value for s in QUOTA_STATUSES]),
        )
        return self._session.scalar(stmt) or 0

    def has_active(self, user_id: int) -> bool:
        stmt = select(SearchJobModel.id).where(
            SearchJobModel.user_id == user_id, SearchJobModel.status.in_([s.value for s in ACTIVE_STATUSES])
        )
        return self._session.scalar(stmt.limit(1)) is not None

    # --- cola ---
    def add(self, job: SearchJob) -> SearchJob:
        row = SearchJobModel(user_id=job.user_id)
        _apply(job, row)
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return _to_entity(row)

    def claim_next(self) -> SearchJob | None:
        """Reclamo atómico: el UPDATE condicional solo prospera si el trabajo seguía en cola, así que dos
        workers nunca ejecutan el mismo trabajo."""
        candidate_id = self._session.scalar(
            select(SearchJobModel.id)
            .where(SearchJobModel.status == SearchStatus.QUEUED.value)
            .order_by(SearchJobModel.id)
            .limit(1)
        )
        if candidate_id is None:
            return None
        claimed = self._session.execute(
            update(SearchJobModel)
            .where(SearchJobModel.id == candidate_id, SearchJobModel.status == SearchStatus.QUEUED.value)
            .values(status=SearchStatus.RUNNING.value, started_at=_now())
        )
        self._session.commit()
        if _rowcount(claimed) != 1:
            return None
        row = self._session.get(SearchJobModel, candidate_id)
        if row is not None:
            self._session.refresh(row)
        return _to_entity(row) if row else None

    def save(self, job: SearchJob) -> SearchJob:
        row = self._session.get(SearchJobModel, job.id)
        if row is None:
            raise LookupError("Trabajo de búsqueda no encontrado")
        _apply(job, row)
        self._session.commit()
        self._session.refresh(row)
        return _to_entity(row)

    def fail_stale(self, older_than: datetime) -> int:
        result = self._session.execute(
            update(SearchJobModel)
            .where(SearchJobModel.status == SearchStatus.RUNNING.value, SearchJobModel.started_at < older_than)
            .values(
                status=SearchStatus.FAILED.value,
                finished_at=_now(),
                error="La búsqueda se interrumpió. No se ha descontado de tu cupo.",
            )
        )
        self._session.commit()
        return _rowcount(result)
