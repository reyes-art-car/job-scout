from typing import Protocol

from job_tracker.domain.candidate.search_profile import SearchProfile


class SearchProfileRepository(Protocol):
    def get(self, user_id: int) -> SearchProfile | None: ...

    def save(self, user_id: int, profile: SearchProfile) -> SearchProfile: ...
