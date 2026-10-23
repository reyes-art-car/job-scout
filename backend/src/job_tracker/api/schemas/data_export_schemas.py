from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from job_tracker.api.schemas.auth_schemas import MAX_PASSWORD_LENGTH
from job_tracker.api.schemas.offer_schemas import OfferOut
from job_tracker.api.schemas.profile_schemas import SearchProfileOut
from job_tracker.api.schemas.search_schemas import SearchJobOut
from job_tracker.application.auth.account_data import AccountExport
from job_tracker.domain.user.entities import Plan
from job_tracker.shared.clock import utc_now


class DeleteAccountRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    password: Annotated[str, StringConstraints(min_length=1, max_length=MAX_PASSWORD_LENGTH)]


class AccountInfoOut(BaseModel):
    email: str
    plan: Plan
    email_verified: bool
    created_at: datetime | None


class SearchJobExportOut(SearchJobOut):
    """En la exportación sí aparece el consumo técnico: es un dato sobre la persona, aunque no se muestre en la app."""

    input_tokens: int
    output_tokens: int
    web_searches: int
    web_fetches: int


class AccountExportOut(BaseModel):
    exported_at: datetime
    account: AccountInfoOut
    profile: SearchProfileOut | None
    offers: list[OfferOut]
    searches: list[SearchJobExportOut]

    @classmethod
    def from_export(cls, data: AccountExport) -> "AccountExportOut":
        user = data.user
        return cls(
            exported_at=utc_now(),
            account=AccountInfoOut(
                email=user.email, plan=user.plan, email_verified=user.email_verified, created_at=user.created_at
            ),
            profile=SearchProfileOut.from_entity(data.profile) if data.profile else None,
            offers=[OfferOut.from_entity(offer) for offer in data.offers],
            searches=[SearchJobExportOut.from_entity(job) for job in data.searches],
        )
