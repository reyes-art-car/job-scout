from job_tracker.domain.offer.entities import Offer
from job_tracker.domain.offer.repository import OfferFilters, OfferRepository, OfferStats


class ListOffers:
    """Caso de uso: depende únicamente del puerto OfferRepository, nunca de SQLAlchemy."""

    def __init__(self, repository: OfferRepository):
        self._repository = repository

    def execute(self, filters: OfferFilters) -> tuple[list[Offer], int]:
        return self._repository.list(filters)

    def stats(self) -> OfferStats:
        return self._repository.stats()
