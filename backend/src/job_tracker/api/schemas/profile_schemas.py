from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from job_tracker.api.schemas.types import Text100, Text255, Text4000
from job_tracker.domain.candidate.search_profile import SearchProfile

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
