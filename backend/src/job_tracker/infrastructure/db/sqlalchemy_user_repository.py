from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from job_tracker.domain.user.entities import Plan, User
from job_tracker.domain.user.exceptions import EmailAlreadyRegisteredError
from job_tracker.infrastructure.db.models import UserModel


def _to_entity(row: UserModel) -> User:
    return User(
        id=row.id, email=row.email, password_hash=row.password_hash, plan=Plan(row.plan), created_at=row.created_at
    )


class SqlAlchemyUserRepository:
    def __init__(self, session: Session):
        self._session = session

    def get(self, user_id: int) -> User | None:
        row = self._session.get(UserModel, user_id)
        return _to_entity(row) if row else None

    def get_by_email(self, email: str) -> User | None:
        row = self._session.scalar(select(UserModel).where(UserModel.email == email))
        return _to_entity(row) if row else None

    def add(self, user: User) -> User:
        row = UserModel(email=user.email, password_hash=user.password_hash, plan=user.plan.value)
        self._session.add(row)
        try:
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            raise EmailAlreadyRegisteredError from exc
        self._session.refresh(row)
        return _to_entity(row)
