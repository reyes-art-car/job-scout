from dataclasses import dataclass
from datetime import date

from job_tracker.domain.offer.entities import KanbanStatus, Offer, OfferSource, Priority
from job_tracker.domain.offer.exceptions import DuplicateOfferError
from job_tracker.domain.offer.repository import OfferRegistry
from job_tracker.domain.offer.scoring import priority_for


@dataclass
class NewOfferData:
    title: str
    company: str
    portal: str = "Otro"
    url: str | None = None
    published_date: date | None = None
    location: str = ""
    modality: str = ""
    contract_type: str = "No especificado"
    salary: str | None = None
    experience_required: str = "No especificado"
    mandatory_tech: str = ""
    desirable_tech: str = ""
    requirements_met: str = ""
    requirements_missing: str = ""
    score_reason: str = ""
    compatibility: int = 0
    kanban_status: KanbanStatus = KanbanStatus.PENDIENTE
    notes: str | None = None
    priority: Priority | None = None
    source: OfferSource = OfferSource.DOCUMENT_UPLOAD


class CreateOffer:
    """Caso de uso: alta de una oferta, con ID secuencial (OF037…) y detección de duplicados por URL."""

    def __init__(self, repository: OfferRegistry):
        self._repository = repository

    def execute(self, data: NewOfferData) -> Offer:
        code = self._repository.next_code()
        if self._repository.exists_by_code_or_url(code, data.url):
            raise DuplicateOfferError(code=code, url=data.url)
        priority = data.priority or priority_for(data.compatibility)
        offer = Offer(
            id=None,
            code=code,
            priority=priority,
            compatibility=data.compatibility,
            title=data.title,
            company=data.company,
            portal=data.portal,
            url=data.url,
            published_date=data.published_date,
            location=data.location,
            modality=data.modality,
            contract_type=data.contract_type,
            salary=data.salary,
            experience_required=data.experience_required,
            mandatory_tech=data.mandatory_tech,
            desirable_tech=data.desirable_tech,
            requirements_met=data.requirements_met,
            requirements_missing=data.requirements_missing,
            score_reason=data.score_reason,
            kanban_status=data.kanban_status,
            adapted_cv_filename=None,
            notes=data.notes,
            source=data.source,
        )
        return self._repository.add(offer)
