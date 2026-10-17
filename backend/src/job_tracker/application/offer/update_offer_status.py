from job_tracker.domain.offer.entities import KanbanStatus, Offer
from job_tracker.domain.offer.repository import OfferWriter


class UpdateOfferStatus:
    def __init__(self, repository: OfferWriter):
        self._repository = repository

    def execute(self, offer_id: int, status: KanbanStatus) -> Offer:
        return self._repository.update_status(offer_id, status)
