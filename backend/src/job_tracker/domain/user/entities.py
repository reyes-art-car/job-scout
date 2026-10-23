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
    # Las acciones que cuestan dinero (buscar ofertas) exigen un email confirmado.
    email_verified: bool = False
    # Se incrementa al cerrar sesión o cambiar la contraseña: invalida todos los tokens emitidos antes.
    token_version: int = 0
    created_at: datetime | None = None
