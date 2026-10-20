"""Traducción de errores de dominio a respuestas HTTP.

Regla de seguridad: el cliente nunca recibe trazas, rutas del servidor, SQL ni el valor que provocó
el error; el detalle se registra en el log con un identificador para poder localizarlo.
"""

import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from job_tracker.application.search.start_search import UnknownStrategyError
from job_tracker.domain.offer.exceptions import (
    CvNotAvailableError,
    DuplicateOfferError,
    OfferNotFoundError,
)
from job_tracker.domain.search.exceptions import (
    ProfileRequiredError,
    SearchAlreadyRunningError,
    SearchJobNotFoundError,
    SearchQuotaExceededError,
)
from job_tracker.domain.user.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    RegistrationClosedError,
)

logger = logging.getLogger("job_tracker.errors")


def _error(status: int, message: str, **extra: object) -> JSONResponse:
    return JSONResponse({"error": message, **extra}, status_code=status)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(OfferNotFoundError)
    async def _not_found(_: Request, __: OfferNotFoundError) -> JSONResponse:
        return _error(404, "Oferta no encontrada")

    @app.exception_handler(CvNotAvailableError)
    async def _cv_missing(_: Request, __: CvNotAvailableError) -> JSONResponse:
        return _error(404, "Esta oferta no tiene un CV adaptado disponible")

    @app.exception_handler(DuplicateOfferError)
    async def _duplicate(_: Request, __: DuplicateOfferError) -> JSONResponse:
        return _error(409, "Ya existe una oferta con esa URL")

    @app.exception_handler(EmailAlreadyRegisteredError)
    async def _email_taken(_: Request, __: EmailAlreadyRegisteredError) -> JSONResponse:
        return _error(409, "Ya existe una cuenta con ese email")

    @app.exception_handler(InvalidCredentialsError)
    async def _bad_credentials(_: Request, __: InvalidCredentialsError) -> JSONResponse:
        response = _error(401, "Email o contraseña incorrectos")
        response.headers["WWW-Authenticate"] = "Bearer"
        return response

    @app.exception_handler(RegistrationClosedError)
    async def _registration_closed(_: Request, __: RegistrationClosedError) -> JSONResponse:
        return _error(403, "El registro de nuevas cuentas está cerrado por ahora")

    @app.exception_handler(ProfileRequiredError)
    async def _profile_required(_: Request, __: ProfileRequiredError) -> JSONResponse:
        return _error(409, "Completa tu perfil de búsqueda antes de buscar ofertas")

    @app.exception_handler(SearchAlreadyRunningError)
    async def _search_running(_: Request, __: SearchAlreadyRunningError) -> JSONResponse:
        return _error(409, "Ya tienes una búsqueda en curso")

    @app.exception_handler(SearchQuotaExceededError)
    async def _quota(_: Request, exc: SearchQuotaExceededError) -> JSONResponse:
        return _error(402, "Has agotado las búsquedas de tu plan este mes", limit=exc.limit)

    @app.exception_handler(SearchJobNotFoundError)
    async def _search_missing(_: Request, __: SearchJobNotFoundError) -> JSONResponse:
        return _error(404, "Búsqueda no encontrada")

    @app.exception_handler(UnknownStrategyError)
    async def _bad_strategy(_: Request, __: UnknownStrategyError) -> JSONResponse:
        return _error(422, "Tipo de búsqueda no válido")

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        # Solo campo y motivo: se omite `input` para no devolver al cliente lo que envió.
        problems = [
            {"field": ".".join(str(part) for part in e["loc"] if part != "body"), "message": e["msg"]}
            for e in exc.errors()
        ]
        return _error(422, "Datos no válidos", problems=problems)


class UnhandledErrorMiddleware:
    """Convierte cualquier excepción no controlada en un 500 genérico.

    Va DENTRO del middleware de cabeceras de seguridad (a diferencia del manejador de `Exception` de
    Starlette, que queda por fuera) para que hasta los errores 500 lleven cabeceras de seguridad.
    """

    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        started = False

        async def tracking_send(message: Message) -> None:
            nonlocal started
            started = started or message["type"] == "http.response.start"
            await send(message)

        try:
            await self._app(scope, receive, tracking_send)
        except Exception as exc:
            incident = uuid.uuid4().hex[:12]
            logger.error("Error no controlado [%s] %s %s", incident, scope["method"], scope["path"], exc_info=exc)
            if started:
                raise
            response = _error(500, "Error interno del servidor", incident=incident)
            await response(scope, receive, send)
