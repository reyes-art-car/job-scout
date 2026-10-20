from dataclasses import dataclass

from job_tracker.application.auth.accounts import VerifyPassword
from job_tracker.domain.candidate.search_profile import SearchProfile
from job_tracker.domain.candidate.search_profile_repository import SearchProfileRepository
from job_tracker.domain.offer.entities import Offer
from job_tracker.domain.offer.repository import OfferFilters, OfferReader
from job_tracker.domain.search.entities import SearchJob
from job_tracker.domain.search.repository import SearchJobReader
from job_tracker.domain.user.entities import User
from job_tracker.domain.user.exceptions import WrongPasswordError
from job_tracker.domain.user.repository import UserRepository

EXPORT_LIMIT = 10_000
SEARCH_HISTORY_LIMIT = 1_000


@dataclass(frozen=True)
class AccountExport:
    user: User
    profile: SearchProfile | None
    offers: list[Offer]
    searches: list[SearchJob]


class ExportAccountData:
    """Todo lo que el servicio guarda de una persona (derecho de acceso y de portabilidad, art. 15 y 20 RGPD).

    Nunca incluye el hash de la contraseña: es un secreto de seguridad, no un dato que la persona haya aportado.
    """

    def __init__(self, offers: OfferReader, profiles: SearchProfileRepository, jobs: SearchJobReader) -> None:
        self._offers = offers
        self._profiles = profiles
        self._jobs = jobs

    def execute(self, user: User) -> AccountExport:
        user_id = user.id or 0
        offers, _ = self._offers.list(OfferFilters(page=1, page_size=EXPORT_LIMIT))
        return AccountExport(
            user=user,
            profile=self._profiles.get(user_id),
            offers=offers,
            searches=self._jobs.list_for_user(user_id, SEARCH_HISTORY_LIMIT),
        )


class DeleteAccount:
    """Borra la cuenta y TODOS sus datos (derecho de supresión, art. 17 RGPD).

    Pide la contraseña actual: una sesión robada no basta para destruir la cuenta de otra persona.
    """

    def __init__(self, users: UserRepository, verify_password: VerifyPassword) -> None:
        self._users = users
        self._verify_password = verify_password

    def execute(self, user: User, password: str) -> None:
        if not self._verify_password(password, user.password_hash):
            raise WrongPasswordError
        self._users.delete(user.id or 0)
