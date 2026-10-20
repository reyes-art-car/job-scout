from typing import Protocol

from job_tracker.domain.user.entities import User


class UserRepository(Protocol):
    def get(self, user_id: int) -> User | None: ...

    def get_by_email(self, email: str) -> User | None: ...

    def add(self, user: User) -> User:
        """Lanza EmailAlreadyRegisteredError si el email ya existe."""
        ...

    def mark_email_verified(self, user_id: int) -> None: ...

    def set_password(self, user_id: int, password_hash: str) -> None:
        """Cambia la contraseña e invalida todas las sesiones y enlaces anteriores (sube `token_version`)."""
        ...

    def delete(self, user_id: int) -> None:
        """Borra la cuenta y todos sus datos: ofertas, perfil, entrevistas y búsquedas."""
        ...

    def revoke_sessions(self, user_id: int) -> None:
        """Invalida todos los tokens emitidos hasta ahora para esa cuenta."""
        ...
