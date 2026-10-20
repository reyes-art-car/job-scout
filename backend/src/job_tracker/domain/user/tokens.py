from enum import StrEnum
from typing import Protocol

from job_tracker.domain.user.entities import User


class ActionKind(StrEnum):
    VERIFY_EMAIL = "verify"
    RESET = "reset"


class ActionTokens(Protocol):
    """Enlaces de un solo propósito que se envían por correo."""

    def issue(self, kind: ActionKind, user: User) -> str: ...

    def read(self, kind: ActionKind, token: str) -> tuple[int, int]:
        """Devuelve (id de usuario, versión de tokens) o lanza InvalidActionTokenError."""
        ...
