from job_tracker.domain.offer.entities import Offer
from job_tracker.domain.offer.repository import OfferFilters, OfferReader, OfferStats, OfferStatsReader


class ListOffers:
    """Caso de uso: depende únicamente del puerto OfferReader, nunca de SQLAlchemy."""

    def __init__(self, repository: OfferReader):
        self._repository = repository

    def execute(self, filters: OfferFilters) -> tuple[list[Offer], int]:
        return self._repository.list(filters)


class GetOfferStats:
    def __init__(self, repository: OfferStatsReader):
        self._repository = repository

    def execute(self) -> OfferStats:
        return self._repository.stats()
