import math

from job_tracker.api.security.rate_limit import SlidingWindowLimiter
from job_tracker.domain.user.exceptions import TooManyAttemptsError

# Tope por cuenta (sumando todas las IPs) respecto al tope por cuenta+IP.
ACCOUNT_WIDE_FACTOR = 5


class LoginThrottle:
    """Bloquea temporalmente los inicios de sesión tras demasiados fallos, con dos niveles.

    - Por cuenta **e IP**: quien falla desde una IP queda bloqueado solo para esa combinación. Así un atacante no puede
      dejar fuera a la víctima real (que entra desde otra IP) con solo fallar a propósito desde la suya.
    - Por cuenta (todas las IPs): un tope más holgado frena el ataque repartido entre muchas IPs.

    Solo cuentan los fallos y un acceso correcto reinicia los contadores de esa IP.
    """

    def __init__(self, *, failures: int, window_minutes: int, limiter: SlidingWindowLimiter | None = None) -> None:
        self._failures = failures
        self._window = window_minutes * 60.0
        self._limiter = limiter or SlidingWindowLimiter()

    @staticmethod
    def _account(email: str) -> str:
        return f"login:{email.strip().lower()}"

    def _pair(self, email: str, ip: str) -> str:
        return f"{self._account(email)}|{ip}"

    def check(self, email: str, ip: str) -> None:
        wait = max(
            self._limiter.peek(self._pair(email, ip), self._failures, self._window),
            self._limiter.peek(self._account(email), self._failures * ACCOUNT_WIDE_FACTOR, self._window),
        )
        if wait > 0:
            raise TooManyAttemptsError(math.ceil(wait))

    def record_failure(self, email: str, ip: str) -> None:
        self._limiter.hit(self._pair(email, ip), self._failures, self._window)
        self._limiter.hit(self._account(email), self._failures * ACCOUNT_WIDE_FACTOR, self._window)

    def reset(self, email: str, ip: str) -> None:
        self._limiter.reset(self._pair(email, ip))
