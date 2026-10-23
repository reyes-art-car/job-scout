"""Tokens JWT (HS256) de vida corta: de sesión y de acciones de un solo propósito (verificar email, restablecer clave).

Cada token lleva un tipo (`typ`) y solo vale para ese uso: un enlace de verificación no sirve como sesión ni al revés.
`ver` es la versión de tokens de la cuenta; si la cuenta la sube (cerrar sesión, cambiar contraseña)
los tokens anteriores dejan de valer.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt

ALGORITHM = "HS256"
ACCESS = "access"
VERIFY_EMAIL = "verify"
RESET_LINK = "reset"


class InvalidTokenError(Exception):
    pass


@dataclass(frozen=True)
class TokenClaims:
    user_id: int
    version: int


def _encode(kind: str, user_id: int, *, secret: str, minutes: int, version: int, now: datetime | None) -> str:
    issued = now or datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "typ": kind,
        "ver": version,
        "iat": issued,
        "exp": issued + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def _decode(token: str, kind: str, *, secret: str) -> TokenClaims:
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM], options={"require": ["exp", "sub", "typ"]})
        if payload["typ"] != kind:
            raise InvalidTokenError
        return TokenClaims(user_id=int(payload["sub"]), version=int(payload.get("ver", 0)))
    except (jwt.PyJWTError, ValueError, KeyError, TypeError) as exc:
        raise InvalidTokenError from exc


def create_access_token(
    user_id: int, *, secret: str, minutes: int, version: int = 0, now: datetime | None = None
) -> str:
    return _encode(ACCESS, user_id, secret=secret, minutes=minutes, version=version, now=now)


def decode_access_token(token: str, *, secret: str) -> TokenClaims:
    """Devuelve el usuario y la versión o lanza InvalidTokenError (firma falsa, caducado, de otro tipo…)."""
    return _decode(token, ACCESS, secret=secret)


def create_action_token(
    kind: str, user_id: int, *, secret: str, minutes: int, version: int = 0, now: datetime | None = None
) -> str:
    return _encode(kind, user_id, secret=secret, minutes=minutes, version=version, now=now)


def decode_action_token(token: str, kind: str, *, secret: str) -> TokenClaims:
    return _decode(token, kind, secret=secret)
