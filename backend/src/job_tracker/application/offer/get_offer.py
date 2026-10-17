from job_tracker.domain.offer.entities import Offer
from job_tracker.domain.offer.exceptions import OfferNotFoundError
from job_tracker.domain.offer.repository import OfferReader


class GetOffer:
    def __init__(self, repository: OfferReader):
        self._repository = repository

    def execute(self, offer_id: int) -> Offer:
        offer = self._repository.get(offer_id)
        if offer is None:
            raise OfferNotFoundError(offer_id)
        return offer
