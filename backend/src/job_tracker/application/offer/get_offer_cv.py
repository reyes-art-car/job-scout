from pathlib import Path
from typing import Protocol

from job_tracker.domain.offer.exceptions import CvNotAvailableError, OfferNotFoundError
from job_tracker.domain.offer.repository import OfferReader


class CvLocator(Protocol):
    """Puerto: encuentra el fichero de un CV adaptado a partir de su nombre."""

    def locate(self, filename: str) -> Path | None: ...


class GetOfferCv:
    def __init__(self, repository: OfferReader, locator: CvLocator):
        self._repository = repository
        self._locator = locator

    def execute(self, offer_id: int) -> Path:
        offer = self._repository.get(offer_id)
        if offer is None:
            raise OfferNotFoundError(offer_id)
        if not offer.adapted_cv_filename:
            raise CvNotAvailableError
        path = self._locator.locate(offer.adapted_cv_filename)
        if path is None:
            raise CvNotAvailableError
        return path
