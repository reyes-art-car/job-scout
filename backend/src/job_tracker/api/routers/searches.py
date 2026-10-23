from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from job_tracker.api.deps import (
    get_app_settings,
    get_current_user,
    get_quota_service,
    get_search_job_queue,
    get_search_job_reader,
    get_search_profile_repository,
)
from job_tracker.api.schemas.search_schemas import SearchJobOut, SearchRequest
from job_tracker.application.search.start_search import GetQuota, StartSearch
from job_tracker.config import Settings
from job_tracker.domain.candidate.search_profile_repository import SearchProfileRepository
from job_tracker.domain.search.exceptions import SearchJobNotFoundError
from job_tracker.domain.search.repository import SearchJobQueue, SearchJobReader
from job_tracker.domain.user.entities import User

router = APIRouter(prefix="/api/searches", tags=["searches"], dependencies=[Depends(get_current_user)])

CurrentUser = Annotated[User, Depends(get_current_user)]
Reader = Annotated[SearchJobReader, Depends(get_search_job_reader)]
Queue = Annotated[SearchJobQueue, Depends(get_search_job_queue)]
Profiles = Annotated[SearchProfileRepository, Depends(get_search_profile_repository)]
Quotas = Annotated[GetQuota, Depends(get_quota_service)]


@router.post("", response_model=SearchJobOut, status_code=status.HTTP_202_ACCEPTED)
def start_search(
    payload: SearchRequest,
    user: CurrentUser,
    reader: Reader,
    queue: Queue,
    profiles: Profiles,
    quotas: Quotas,
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> SearchJobOut:
    """Encola una búsqueda. El worker la ejecuta; el cliente consulta su estado con GET /api/searches/{id}."""
    job = StartSearch(reader, queue, profiles, quotas, settings.max_searches_per_day).execute(user, payload.strategy)
    return SearchJobOut.from_entity(job)


@router.get("", response_model=list[SearchJobOut])
def list_searches(
    user: CurrentUser, reader: Reader, limit: Annotated[int, Query(ge=1, le=50)] = 20
) -> list[SearchJobOut]:
    return [SearchJobOut.from_entity(job) for job in reader.list_for_user(user.id or 0, limit)]


@router.get("/{job_id}", response_model=SearchJobOut)
def get_search(job_id: int, user: CurrentUser, reader: Reader) -> SearchJobOut:
    job = reader.get(user.id or 0, job_id)
    if job is None:
        raise SearchJobNotFoundError
    return SearchJobOut.from_entity(job)
