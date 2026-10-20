from job_tracker.api.security.rate_limit import SlidingWindowLimiter

HOUR_SECONDS = 3600.0


class EmailThrottle:
    """Limita cuántos correos de cuenta (verificación, restablecer clave) se envían a la misma dirección.

    Evita que la API se use para inundar el buzón de un tercero. Al superar el límite el envío se omite en silencio:
    la respuesta HTTP es la misma, así que tampoco revela nada.
    """

    def __init__(self, *, per_hour: int, limiter: SlidingWindowLimiter | None = None) -> None:
        self._per_hour = per_hour
        self._limiter = limiter or SlidingWindowLimiter()

    def allow(self, kind: str, email: str) -> bool:
        return self._limiter.hit(f"{kind}:{email.strip().lower()}", self._per_hour, HOUR_SECONDS) == 0
