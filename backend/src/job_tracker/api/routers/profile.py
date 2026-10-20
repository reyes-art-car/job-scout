from typing import Annotated

from fastapi import APIRouter, Depends

from job_tracker.api.deps import get_current_user, get_search_profile_repository
from job_tracker.api.schemas.profile_schemas import SearchProfileIn, SearchProfileOut
from job_tracker.domain.candidate.search_profile_repository import SearchProfileRepository
from job_tracker.domain.user.entities import User

router = APIRouter(prefix="/api/profile", tags=["profile"], dependencies=[Depends(get_current_user)])

Profiles = Annotated[SearchProfileRepository, Depends(get_search_profile_repository)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("", response_model=SearchProfileOut | None)
def get_profile(user: CurrentUser, profiles: Profiles) -> SearchProfileOut | None:
    """Perfil de búsqueda del usuario, o null si aún no lo ha rellenado."""
    profile = profiles.get(user.id or 0)
    return SearchProfileOut.from_entity(profile) if profile else None


@router.put("", response_model=SearchProfileOut)
def put_profile(payload: SearchProfileIn, user: CurrentUser, profiles: Profiles) -> SearchProfileOut:
    return SearchProfileOut.from_entity(profiles.save(user.id or 0, payload.to_entity()))
