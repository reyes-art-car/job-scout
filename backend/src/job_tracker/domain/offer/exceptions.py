class OfferNotFoundError(Exception):
    def __init__(self, offer_id: int):
        super().__init__(f"No existe ninguna oferta con id={offer_id}")
        self.offer_id = offer_id


class DuplicateOfferError(Exception):
    def __init__(self, code: str | None = None, url: str | None = None):
        super().__init__(f"Oferta duplicada (code={code!r}, url={url!r})")
        self.code = code
        self.url = url
