from job_tracker.application.auth.accounts import HashPassword, normalize_email
from job_tracker.domain.user.entities import User
from job_tracker.domain.user.exceptions import InvalidActionTokenError
from job_tracker.domain.user.repository import UserRepository
from job_tracker.domain.user.tokens import ActionKind, ActionTokens


class VerifyEmail:
    """Confirma el email con el enlace recibido. Es idempotente: repetir el enlace no hace daño."""

    def __init__(self, users: UserRepository, tokens: ActionTokens) -> None:
        self._users = users
        self._tokens = tokens

    def execute(self, token: str) -> None:
        user_id, _ = self._tokens.read(ActionKind.VERIFY_EMAIL, token)
        if self._users.get(user_id) is None:
            raise InvalidActionTokenError
        self._users.mark_email_verified(user_id)


class RequestPasswordReset:
    """Localiza la cuenta a la que enviar el enlace. Devuelve None si no existe (el llamador responde igual)."""

    def __init__(self, users: UserRepository) -> None:
        self._users = users

    def execute(self, email: str) -> User | None:
        return self._users.get_by_email(normalize_email(email))


class ResetPassword:
    """Cambia la contraseña con el enlace recibido y cierra todas las sesiones abiertas.

    El enlace lleva la versión de tokens de la cuenta en el momento de emitirse; al cambiar la contraseña esa versión
    sube, así que el mismo enlace no vale una segunda vez.
    """

    def __init__(self, users: UserRepository, tokens: ActionTokens, hash_password: HashPassword) -> None:
        self._users = users
        self._tokens = tokens
        self._hash_password = hash_password

    def execute(self, token: str, new_password: str) -> None:
        user_id, version = self._tokens.read(ActionKind.RESET, token)
        user = self._users.get(user_id)
        if user is None or user.token_version != version:
            raise InvalidActionTokenError
        self._users.set_password(user_id, self._hash_password(new_password))
