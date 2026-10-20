from collections.abc import Generator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from job_tracker.application.offer.get_offer_cv import CvLocator
from job_tracker.application.search.start_search import GetQuota
from job_tracker.config import Settings
from job_tracker.domain.candidate.profile import CandidateProfile, load_candidate_profile
from job_tracker.domain.candidate.search_profile_repository import SearchProfileRepository
from job_tracker.domain.interview.repository import InterviewRepository
from job_tracker.domain.offer.repository import OfferRepository
from job_tracker.domain.search.repository import SearchJobQueue, SearchJobReader
from job_tracker.domain.user.entities import User
from job_tracker.domain.user.repository import UserRepository
from job_tracker.infrastructure.db.base import get_db_session
from job_tracker.infrastructure.db.sqlalchemy_interview_repository import (
    SqlAlchemyInterviewRepository,
)
from job_tracker.infrastructure.db.sqlalchemy_offer_repository import SqlAlchemyOfferRepository
from job_tracker.infrastructure.db.sqlalchemy_search_job_repository import SqlAlchemySearchJobRepository
from job_tracker.infrastructure.db.sqlalchemy_search_profile_repository import SqlAlchemySearchProfileRepository
from job_tracker.infrastructure.db.sqlalchemy_user_repository import SqlAlchemyUserRepository
from job_tracker.infrastructure.files.cv_locator import DirectoryCvLocator
from job_tracker.infrastructure.security.tokens import InvalidTokenError, decode_access_token

_bearer = HTTPBearer(auto_error=False, description="Token de acceso obtenido en /api/auth/login")


def get_app_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def get_db(db: Session = Depends(get_db_session)) -> Generator[Session, None, None]:
    yield db


# Las dependencias devuelven el puerto (Protocol), no el adaptador concreto: los routers
# no saben que hay SQLAlchemy detrás.
def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return SqlAlchemyUserRepository(db)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    settings: Settings = Depends(get_app_settings),
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    users: UserRepository = Depends(get_user_repository),
) -> User:
    """Usuario autenticado por el token Bearer. Denegado por defecto: sin token válido, 401.

    Se vuelve a leer el usuario de la BD en cada petición, así una cuenta borrada pierde el acceso
    aunque su token no haya caducado.
    """
    if credentials is None or settings.jwt_secret is None:
        raise _unauthorized()
    try:
        user_id = decode_access_token(credentials.credentials, secret=settings.jwt_secret.get_secret_value())
    except InvalidTokenError:
        raise _unauthorized() from None
    user = users.get(user_id)
    if user is None:
        raise _unauthorized()
    return user


def get_offer_repository(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> OfferRepository:
    return SqlAlchemyOfferRepository(db, user.id or 0)


def get_interview_repository(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> InterviewRepository:
    return SqlAlchemyInterviewRepository(db, user.id or 0)


def get_search_profile_repository(db: Session = Depends(get_db)) -> SearchProfileRepository:
    return SqlAlchemySearchProfileRepository(db)


def get_search_job_repository(db: Session = Depends(get_db)) -> SqlAlchemySearchJobRepository:
    return SqlAlchemySearchJobRepository(db)


def get_search_job_reader(jobs: SqlAlchemySearchJobRepository = Depends(get_search_job_repository)) -> SearchJobReader:
    return jobs


def get_search_job_queue(jobs: SqlAlchemySearchJobRepository = Depends(get_search_job_repository)) -> SearchJobQueue:
    return jobs


def get_quota_service(
    settings: Settings = Depends(get_app_settings), jobs: SearchJobReader = Depends(get_search_job_reader)
) -> GetQuota:
    return GetQuota(jobs, settings.searches_per_month)


def get_cv_locator(settings: Settings = Depends(get_app_settings)) -> CvLocator:
    return DirectoryCvLocator(settings.cv_output_dir)


def get_profile(settings: Settings = Depends(get_app_settings)) -> CandidateProfile:
    return load_candidate_profile(settings.resolved_candidate_profile_path)
