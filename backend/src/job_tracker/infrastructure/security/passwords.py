"""Hash de contraseñas con scrypt (biblioteca estándar, sin dependencias nuevas).

Formato guardado: `scrypt$N$r$p$salt_b64$hash_b64`. Los parámetros viajan con el hash para poder
subirlos en el futuro sin invalidar las contraseñas ya guardadas.
"""

import base64
import hashlib
import hmac
import secrets

_N, _R, _P = 2**14, 8, 1
_KEY_LEN = 32
_SALT_LEN = 16
_MAX_MEMORY = 64 * 1024 * 1024


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _derive(password: str, salt: bytes, n: int, r: int, p: int) -> bytes:
    return hashlib.scrypt(password.encode(), salt=salt, n=n, r=r, p=p, dklen=_KEY_LEN, maxmem=_MAX_MEMORY)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(_SALT_LEN)
    return f"scrypt${_N}${_R}${_P}${_b64(salt)}${_b64(_derive(password, salt, _N, _R, _P))}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt_b64, hash_b64 = stored.split("$")
        if scheme != "scrypt":
            return False
        expected = base64.b64decode(hash_b64)
        candidate = _derive(password, base64.b64decode(salt_b64), int(n), int(r), int(p))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(candidate, expected)


# Hash de una contraseña inexistente: se verifica contra él cuando el email no existe para que el
# tiempo de respuesta no delate qué emails están registrados.
DUMMY_HASH = hash_password(secrets.token_urlsafe(16))
