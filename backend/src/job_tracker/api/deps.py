from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from job_tracker.config import Settings, get_settings
from job_tracker.domain.candidate.profile import CandidateProfile, load_candidate_profile
from job_tracker.infrastructure.db.base import get_db_session
from job_tracker.infrastructure.db.sqlalchemy_interview_repository import (
    SqlAlchemyInterviewRepository,
)
from job_tracker.infrastructure.db.sqlalchemy_offer_repository import SqlAlchemyOfferRepository


def get_db(db: Session = Depends(get_db_session)) -> Generator[Session, None, None]:
    yield db


def get_offer_repository(db: Session = Depends(get_db)) -> SqlAlchemyOfferRepository:
    return SqlAlchemyOfferRepository(db)


def get_interview_repository(db: Session = Depends(get_db)) -> SqlAlchemyInterviewRepository:
    return SqlAlchemyInterviewRepository(db)


def get_app_settings() -> Settings:
    return get_settings()


def get_profile(settings: Settings = Depends(get_app_settings)) -> CandidateProfile:
    return load_candidate_profile(settings.resolved_candidate_profile_path)
