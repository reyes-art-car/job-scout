from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from job_tracker.application.search.prompt import STRATEGIES
from job_tracker.domain.candidate.search_profile_repository import SearchProfileRepository
from job_tracker.domain.search.entities import SearchJob
from job_tracker.domain.search.exceptions import (
    ProfileRequiredError,
    SearchAlreadyRunningError,
    SearchQuotaExceededError,
)
from job_tracker.domain.search.repository import SearchJobQueue, SearchJobReader
from job_tracker.domain.user.entities import User


class UnknownStrategyError(ValueError):
    pass


@dataclass(frozen=True)
class Quota:
    limit: int
    used: int

    @property
    def remaining(self) -> int:
        return max(0, self.limit - self.used)


def month_start(now: datetime) -> datetime:
    return datetime(now.year, now.month, 1)


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class GetQuota:
    """Cupo mensual de búsquedas del plan del usuario."""

    def __init__(self, jobs: SearchJobReader, limit_for_plan: Callable[[str], int]):
        self._jobs = jobs
        self._limit_for_plan = limit_for_plan

    def execute(self, user: User, now: datetime | None = None) -> Quota:
        now = now or utc_now()
        used = self._jobs.count_quota_used_since(user.id or 0, month_start(now))
        return Quota(limit=self._limit_for_plan(user.plan.value), used=used)


class StartSearch:
    """Caso de uso: encola una búsqueda si el usuario tiene perfil, cupo y ninguna otra en curso."""

    def __init__(
        self,
        jobs: SearchJobReader,
        queue: SearchJobQueue,
        profiles: SearchProfileRepository,
        quota: GetQuota,
    ):
        self._jobs = jobs
        self._queue = queue
        self._profiles = profiles
        self._quota = quota

    def execute(self, user: User, strategy: str, now: datetime | None = None) -> SearchJob:
        if strategy not in STRATEGIES:
            raise UnknownStrategyError(strategy)
        user_id = user.id or 0
        if self._profiles.get(user_id) is None:
            raise ProfileRequiredError
        if self._jobs.has_active(user_id):
            raise SearchAlreadyRunningError
        quota = self._quota.execute(user, now)
        if quota.remaining <= 0:
            raise SearchQuotaExceededError(quota.limit)
        return self._queue.add(SearchJob(id=None, user_id=user_id, strategy=strategy))
