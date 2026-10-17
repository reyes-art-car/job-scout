from collections.abc import Iterable

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

_BASE_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    # La API solo devuelve JSON/CSV: no necesita cargar ningún recurso.
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    # Las respuestas contienen datos personales de candidaturas: que ningún intermediario las guarde.
    "Cache-Control": "no-store",
}
_HSTS = "max-age=31536000; includeSubDomains"


class SecurityHeadersMiddleware:
    """Añade cabeceras de seguridad a todas las respuestas HTTP (ASGI puro, sin buffering)."""

    def __init__(self, app: ASGIApp, *, hsts: bool, relaxed_paths: Iterable[str] = ()) -> None:
        self._app = app
        self._hsts = hsts
        # Rutas con interfaz propia (Swagger UI en desarrollo) que necesitan una CSP menos estricta.
        self._relaxed_paths = tuple(relaxed_paths)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        relaxed = scope["path"].startswith(self._relaxed_paths) if self._relaxed_paths else False

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                for name, value in _BASE_HEADERS.items():
                    if relaxed and name in {"Content-Security-Policy", "Cache-Control"}:
                        continue
                    headers.setdefault(name, value)
                if self._hsts:
                    headers.setdefault("Strict-Transport-Security", _HSTS)
            await send(message)

        await self._app(scope, receive, send_with_headers)
