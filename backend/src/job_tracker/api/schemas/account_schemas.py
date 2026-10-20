import re
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints

from job_tracker.api.schemas.types import Text100, Text255, Text4000
from job_tracker.domain.candidate.search_profile import SearchProfile
from job_tracker.domain.search.entities import SearchJob, SearchStatus
from job_tracker.domain.user.entities import Plan

MIN_PASSWORD_LENGTH = 10
MAX_PASSWORD_LENGTH = 128  # evita que una contraseña enorme se use para agotar CPU en el hash
_EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,189}\.[^@\s.]{2,}$")


def _validate_email(value: str) -> str:
    email = value.strip().lower()
    if not _EMAIL.fullmatch(email):
        raise ValueError("Email no válido")
    return email


Email = Annotated[str, StringConstraints(max_length=254), AfterValidator(_validate_email)]
Password = Annotated[str, StringConstraints(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)]


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: Email
    password: Password


class LoginRequest(BaseModel):
    """En el login no se valida la longitud mínima: la política solo se aplica al crear la contraseña."""

    model_config = ConfigDict(extra="forbid")

    email: Email
    password: Annotated[str, StringConstraints(min_length=1, max_length=MAX_PASSWORD_LENGTH)]


class QuotaOut(BaseModel):
    limit: int
    used: int
    remaining: int


class UserOut(BaseModel):
    email: str
    plan: Plan
    quota: QuotaOut


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105
    user: UserOut


List10 = Annotated[list[Text100], Field(max_length=10)]
List20 = Annotated[list[Text100], Field(max_length=20)]


class SearchProfileIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    headline: Annotated[Text255, StringConstraints(min_length=2)]
    seniority: Text100 = "junior"
    summary: Annotated[Text4000, StringConstraints(min_length=10)]
    skills: List20 = Field(default_factory=list)
    target_roles: List10 = Field(default_factory=list)
    search_terms: List10 = Field(default_factory=list)
    country: Text100 = "España"
    onsite_cities: List10 = Field(default_factory=list)
    accepts_hybrid: bool = True
    remote_only: bool = False
    languages: List10 = Field(default_factory=list)
    max_years_experience: int = Field(default=5, ge=0, le=30)

    def to_entity(self) -> SearchProfile:
        return SearchProfile(**self.model_dump())


class SearchProfileOut(SearchProfileIn):
    @classmethod
    def from_entity(cls, profile: SearchProfile) -> "SearchProfileOut":
        return cls(**profile.__dict__)


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy: str = "general"


class SearchJobOut(BaseModel):
    id: int
    strategy: str
    status: SearchStatus
    created_at: datetime | None
    started_at: datetime | None
    finished_at: datetime | None
    offers_added: int
    offers_skipped: int
    error: str | None

    @classmethod
    def from_entity(cls, job: SearchJob) -> "SearchJobOut":
        # No se expone el consumo de tokens al usuario: es un dato interno de coste.
        return cls.model_validate(job, from_attributes=True)
