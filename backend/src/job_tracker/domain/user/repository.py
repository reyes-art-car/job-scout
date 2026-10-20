from typing import Protocol

from job_tracker.domain.user.entities import User


class UserRepository(Protocol):
    def get(self, user_id: int) -> User | None: ...

    def get_by_email(self, email: str) -> User | None: ...

    def add(self, user: User) -> User:
        """Lanza EmailAlreadyRegisteredError si el email ya existe."""
        ...
