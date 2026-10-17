from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class _BodyTooLargeError(Exception):
    pass


class BodySizeLimitMiddleware:
    """Rechaza cuerpos mayores que `max_bytes`, tanto por Content-Length como en transferencias por fragmentos."""

    def __init__(self, app: ASGIApp, *, max_bytes: int) -> None:
        self._app = app
        self._max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        declared = _content_length(scope)
        if declared is _INVALID:
            await _reject(scope, receive, send, 400, "Content-Length no válido")
            return
        if isinstance(declared, int) and declared > self._max_bytes:
            await _reject(scope, receive, send, 413, "Cuerpo de la petición demasiado grande")
            return

        received = 0
        response_started = False

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self._max_bytes:
                    raise _BodyTooLargeError
            return message

        async def tracking_send(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self._app(scope, limited_receive, tracking_send)
        except _BodyTooLargeError:
            if not response_started:
                await _reject(scope, receive, send, 413, "Cuerpo de la petición demasiado grande")


_INVALID = object()


def _content_length(scope: Scope) -> int | object | None:
    for name, value in scope["headers"]:
        if name == b"content-length":
            try:
                length = int(value)
            except ValueError:
                return _INVALID
            return length if length >= 0 else _INVALID
    return None


async def _reject(scope: Scope, receive: Receive, send: Send, status: int, message: str) -> None:
    await JSONResponse({"error": message}, status_code=status)(scope, receive, send)
