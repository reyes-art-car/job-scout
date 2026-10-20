"""Tokens de acceso JWT (HS256) de vida corta."""

from datetime import UTC, datetime, timedelta

import jwt

ALGORITHM = "HS256"


class InvalidTokenError(Exception):
    pass


def create_access_token(user_id: int, *, secret: str, minutes: int, now: datetime | None = None) -> str:
    issued = now or datetime.now(UTC)
    payload = {"sub": str(user_id), "iat": issued, "exp": issued + timedelta(minutes=minutes)}
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def decode_access_token(token: str, *, secret: str) -> int:
    """Devuelve el id de usuario o lanza InvalidTokenError (firma falsa, caducado, mal formado…)."""
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM], options={"require": ["exp", "sub"]})
        return int(payload["sub"])
    except (jwt.PyJWTError, ValueError, KeyError) as exc:
        raise InvalidTokenError from exc
