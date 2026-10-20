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


# Puertos pequeños y específicos (segregación de interfaces): cada caso de uso depende solo de lo que usa.


class OfferReader(Protocol):
    def list(self, filters: OfferFilters) -> tuple[list[Offer], int]:
        """Devuelve (ofertas de la página solicitada, total de resultados sin paginar)."""
        ...

    def get(self, offer_id: int) -> Offer | None: ...

    def get_by_code(self, code: str) -> Offer | None: ...


class OfferStatsReader(Protocol):
    def stats(self) -> OfferStats: ...


class OfferWriter(Protocol):
    def add(self, offer: Offer) -> Offer: ...

    def update(self, offer: Offer) -> Offer: ...

    def update_status(self, offer_id: int, status: KanbanStatus) -> Offer: ...


class OfferIdentity(Protocol):
    def exists_by_code_or_url(self, code: str, url: str | None) -> bool: ...

    def known_urls(self, limit: int) -> list[str]:
        """URLs ya guardadas del usuario (las más recientes primero), para que el buscador no las repita."""
        ...

    def next_code(self) -> str:
        """Siguiente ID secuencial tipo OF037, igual que get_existing_urls_and_last_id() del buscador."""
        ...


class OfferEditor(OfferReader, OfferWriter, Protocol):
    """Leer y guardar: lo que necesita la edición de una oferta."""


class OfferRegistry(OfferIdentity, OfferWriter, Protocol):
    """Identidad y escritura: lo que necesitan el alta y los importadores."""


class OfferRepository(OfferReader, OfferStatsReader, OfferWriter, OfferIdentity, Protocol):
    """Contrato completo que implementa el adaptador de persistencia."""
