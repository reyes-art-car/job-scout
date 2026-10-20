from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Plan(StrEnum):
    FREE = "free"
    PRO = "pro"


@dataclass
class User:
    """Cuenta de usuario. El hash de la contraseña nunca sale de la capa de aplicación."""

    id: int | None
    email: str
    password_hash: str
    plan: Plan = Plan.FREE
    created_at: datetime | None = None
