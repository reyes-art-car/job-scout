import math
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

WINDOW_SECONDS = 60.0
_WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_EXEMPT_PATHS = frozenset({"/api/health"})
_AUTH_PATHS = frozenset({"/api/auth/login", "/api/auth/register"})


@dataclass(frozen=True)
class Limits:
    """Peticiones máximas por IP y minuto para cada tipo de operación."""

    reads: int
    writes: int
    exports: int
    auth: int = 10  # intentos de registro/login por IP y minuto: frena la fuerza bruta de contraseñas


class SlidingWindowLimiter:
    """Limitador de ventana deslizante en memoria (válido para una sola instancia del servidor).

    Con varias réplicas habría que moverlo a Redis o al proxy inverso (ver docs/SECURITY.md).
    """

    def __init__(self, *, max_keys: int = 10_000, clock: Callable[[], float] = time.monotonic) -> None:
        self._hits: dict[str, deque[float]] = {}
        self._max_keys = max_keys
        self._clock = clock

    def hit(self, key: str, limit: int, window: float = WINDOW_SECONDS) -> float:
        """Registra una petición. Devuelve 0 si se permite o los segundos a esperar si se excede."""
        now = self._clock()
        if len(self._hits) >= self._max_keys and key not in self._hits:
            self._evict_expired(now, window)
        timestamps = self._hits.setdefault(key, deque())
        while timestamps and now - timestamps[0] >= window:
            timestamps.popleft()
        if len(timestamps) >= limit:
            return window - (now - timestamps[0])
        timestamps.append(now)
        return 0.0

    def _evict_expired(self, now: float, window: float) -> None:
        for stale in [k for k, ts in self._hits.items() if not ts or now - ts[-1] >= window]:
            del self._hits[stale]


def client_ip(scope: Scope, *, trust_proxy: bool) -> str:
    """IP del cliente. Con proxy de confianza se usa el ÚLTIMO valor de X-Forwarded-For: es el que añade
    nuestro proxy; los anteriores los controla el cliente y se pueden falsear."""
    if trust_proxy:
        for name, value in scope["headers"]:
            if name == b"x-forwarded-for":
                last: str = value.decode("latin-1").split(",")[-1].strip()
                if last:
                    return last
    client = scope.get("client")
    return str(client[0]) if client else "unknown"


class RateLimitMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        limits: Limits,
        trust_proxy: bool,
        limiter: SlidingWindowLimiter | None = None,
    ) -> None:
        self._app = app
        self._limits = limits
        self._trust_proxy = trust_proxy
        self._limiter = limiter or SlidingWindowLimiter()

    def _bucket(self, method: str, path: str) -> tuple[str, int] | None:
        if path in _EXEMPT_PATHS or method == "OPTIONS":
            return None
        if path in _AUTH_PATHS:
            return "auth", self._limits.auth
        if path.endswith("/export.csv"):
            return "export", self._limits.exports
        if method in _WRITE_METHODS:
            return "write", self._limits.writes
        return "read", self._limits.reads

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        bucket = self._bucket(scope["method"], scope["path"])
        if bucket is not None:
            name, limit = bucket
            key = f"{client_ip(scope, trust_proxy=self._trust_proxy)}:{name}"
            retry_after = self._limiter.hit(key, limit)
            if retry_after > 0:
                response = JSONResponse(
                    {"error": "Demasiadas peticiones. Inténtalo de nuevo en unos segundos."},
                    status_code=429,
                    headers={"Retry-After": str(math.ceil(retry_after))},
                )
                await response(scope, receive, send)
                return
        await self._app(scope, receive, send)
