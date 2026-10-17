from dataclasses import dataclass, replace

from job_tracker.domain.offer.entities import KanbanStatus, Offer
from job_tracker.domain.offer.exceptions import OfferNotFoundError
from job_tracker.domain.offer.repository import OfferEditor


@dataclass(frozen=True)
class OfferChanges:
    """Campos editables de una oferta; los `None` no se modifican."""

    notes: str | None = None
    salary: str | None = None
    kanban_status: KanbanStatus | None = None


class UpdateOffer:
    def __init__(self, repository: OfferEditor):
        self._repository = repository

    def execute(self, offer_id: int, changes: OfferChanges) -> Offer:
        offer = self._repository.get(offer_id)
        if offer is None:
            raise OfferNotFoundError(offer_id)
        updated = replace(
            offer,
            notes=offer.notes if changes.notes is None else changes.notes,
            salary=offer.salary if changes.salary is None else changes.salary,
            kanban_status=changes.kanban_status or offer.kanban_status,
        )
        return self._repository.update(updated)
