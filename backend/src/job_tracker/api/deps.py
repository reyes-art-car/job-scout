from collections.abc import Generator

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from job_tracker.application.offer.get_offer_cv import CvLocator
from job_tracker.config import Settings
from job_tracker.domain.candidate.profile import CandidateProfile, load_candidate_profile
from job_tracker.domain.interview.repository import InterviewRepository
from job_tracker.domain.offer.repository import OfferRepository
from job_tracker.infrastructure.db.base import get_db_session
from job_tracker.infrastructure.db.sqlalchemy_interview_repository import (
    SqlAlchemyInterviewRepository,
)
from job_tracker.infrastructure.db.sqlalchemy_offer_repository import SqlAlchemyOfferRepository
from job_tracker.infrastructure.files.cv_locator import DirectoryCvLocator


def get_app_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def get_db(db: Session = Depends(get_db_session)) -> Generator[Session, None, None]:
    yield db


# Las dependencias devuelven el puerto (Protocol), no el adaptador concreto: los routers
# no saben que hay SQLAlchemy detrás.
def get_offer_repository(db: Session = Depends(get_db)) -> OfferRepository:
    return SqlAlchemyOfferRepository(db)


def get_interview_repository(db: Session = Depends(get_db)) -> InterviewRepository:
    return SqlAlchemyInterviewRepository(db)


def get_cv_locator(settings: Settings = Depends(get_app_settings)) -> CvLocator:
    return DirectoryCvLocator(settings.cv_output_dir)


def get_profile(settings: Settings = Depends(get_app_settings)) -> CandidateProfile:
    return load_candidate_profile(settings.resolved_candidate_profile_path)
