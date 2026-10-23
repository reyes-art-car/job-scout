from collections.abc import Callable

from job_tracker.domain.user.entities import User
from job_tracker.domain.user.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    RegistrationClosedError,
)
from job_tracker.domain.user.repository import UserRepository

HashPassword = Callable[[str], str]
VerifyPassword = Callable[[str, str], bool]


def normalize_email(email: str) -> str:
    return email.strip().lower()


class RegisterUser:
    """Alta de cuenta. Quien se registra empieza siempre en el plan gratuito y con el email sin verificar.

    No revela si el email ya existía: devuelve `None` en ese caso y el llamador responde igual en los dos. El coste del
    hash se paga siempre, para que el tiempo de respuesta tampoco lo delate.
    """

    def __init__(self, users: UserRepository, hash_password: HashPassword, *, registration_open: bool):
        self._users = users
        self._hash_password = hash_password
        self._open = registration_open

    def execute(self, email: str, password: str) -> User | None:
        if not self._open:
            raise RegistrationClosedError
        password_hash = self._hash_password(password)
        try:
            return self._users.add(User(id=None, email=normalize_email(email), password_hash=password_hash))
        except EmailAlreadyRegisteredError:
            return None


class AuthenticateUser:
    """Comprueba email y contraseña. Un email desconocido cuesta lo mismo que una contraseña incorrecta."""

    def __init__(self, users: UserRepository, verify_password: VerifyPassword, dummy_hash: str):
        self._users = users
        self._verify_password = verify_password
        self._dummy_hash = dummy_hash

    def execute(self, email: str, password: str) -> User:
        user = self._users.get_by_email(normalize_email(email))
        if user is None:
            self._verify_password(password, self._dummy_hash)
            raise InvalidCredentialsError
        if not self._verify_password(password, user.password_hash):
            raise InvalidCredentialsError
        return user
