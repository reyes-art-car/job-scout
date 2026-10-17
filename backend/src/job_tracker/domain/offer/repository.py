from dataclasses import dataclass
from typing import Protocol

from job_tracker.domain.offer.entities import KanbanStatus, Offer, Priority


@dataclass
class OfferFilters:
    priority: Priority | None = None
    kanban_status: KanbanStatus | None = None
    min_compatibility: int | None = None
    max_compatibility: int | None = None
    portal: str | None = None
    search: str | None = None
    page: int = 1
    page_size: int = 50


@dataclass
class OfferStats:
    total: int
    high_priority: int
    by_status: dict[str, int]


class OfferRepository(Protocol):
    """Puerto del dominio: define el contrato de persistencia sin conocer
    el motor de almacenamiento. Implementado por un adaptador en infrastructure/db.
    """

    def list(self, filters: OfferFilters) -> tuple[list[Offer], int]:
        """Devuelve (ofertas de la página solicitada, total de resultados sin paginar)."""
        ...

    def get(self, offer_id: int) -> Offer | None: ...

    def get_by_code(self, code: str) -> Offer | None: ...

    def exists_by_code_or_url(self, code: str, url: str | None) -> bool: ...

    def add(self, offer: Offer) -> Offer: ...

    def update(self, offer: Offer) -> Offer: ...

    def update_status(self, offer_id: int, status: KanbanStatus) -> Offer: ...

    def next_code(self) -> str:
        """Genera el siguiente ID secuencial tipo OF037, igual que
        get_existing_urls_and_last_id() en busqueda_diaria.py."""
        ...

    def stats(self) -> OfferStats: ...
