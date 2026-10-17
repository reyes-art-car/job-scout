class OfferNotFoundError(Exception):
    def __init__(self, offer_id: int):
        super().__init__(f"No existe ninguna oferta con id={offer_id}")
        self.offer_id = offer_id


class DuplicateOfferError(Exception):
    """Ya existe una oferta con el mismo ID o la misma URL."""

    def __init__(self, code: str | None = None, url: str | None = None):
        super().__init__("Oferta duplicada")
        self.code = code
        self.url = url


class CvNotAvailableError(Exception):
    """La oferta no tiene un CV adaptado o el fichero no está disponible."""
