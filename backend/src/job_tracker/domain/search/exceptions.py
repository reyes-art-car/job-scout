class SearchAlreadyRunningError(Exception):
    pass


class SearchQuotaExceededError(Exception):
    def __init__(self, limit: int):
        super().__init__(f"Has agotado las {limit} búsquedas de tu plan este mes")
        self.limit = limit


class SearchCapacityError(Exception):
    """El servicio ha alcanzado su tope diario global de búsquedas (freno de coste)."""


class ProfileRequiredError(Exception):
    pass


class SearchJobNotFoundError(Exception):
    pass


class LlmError(RuntimeError):
    """El modelo no pudo completar la búsqueda (red, cuota de la API, respuesta vacía…)."""
