from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from job_tracker.domain.user.entities import Plan, User
from job_tracker.domain.user.exceptions import EmailAlreadyRegisteredError
from job_tracker.infrastructure.db.models import (
    ChatMessageModel,
    InterviewSessionModel,
    OfferModel,
    SearchJobModel,
    SearchProfileModel,
    UserModel,
)


def _to_entity(row: UserModel) -> User:
    return User(
        id=row.id,
        email=row.email,
        password_hash=row.password_hash,
        plan=Plan(row.plan),
        email_verified=row.email_verified,
        token_version=row.token_version,
        created_at=row.created_at,
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
        row = UserModel(
            email=user.email,
            password_hash=user.password_hash,
            plan=user.plan.value,
            email_verified=user.email_verified,
            token_version=user.token_version,
        )
        self._session.add(row)
        try:
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            raise EmailAlreadyRegisteredError from exc
        self._session.refresh(row)
        return _to_entity(row)

    def mark_email_verified(self, user_id: int) -> None:
        self._session.execute(update(UserModel).where(UserModel.id == user_id).values(email_verified=True))
        self._session.commit()

    def set_password(self, user_id: int, password_hash: str) -> None:
        # La suma se hace en SQL para que dos cambios simultáneos no pisen el mismo valor.
        self._session.execute(
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(password_hash=password_hash, token_version=UserModel.token_version + 1)
        )
        self._session.commit()

    def delete(self, user_id: int) -> None:
        # Explícito y en una sola transacción: SQLite no aplica ON DELETE CASCADE salvo que se active por conexión,
        # y un borrado a medias dejaría datos personales huérfanos.
        sessions = select(InterviewSessionModel.id).where(InterviewSessionModel.user_id == user_id)
        self._session.execute(delete(ChatMessageModel).where(ChatMessageModel.session_id.in_(sessions)))
        for model in (InterviewSessionModel, OfferModel, SearchJobModel):
            self._session.execute(delete(model).where(model.user_id == user_id))
        self._session.execute(delete(SearchProfileModel).where(SearchProfileModel.user_id == user_id))
        self._session.execute(delete(UserModel).where(UserModel.id == user_id))
        self._session.commit()

    def revoke_sessions(self, user_id: int) -> None:
        self._session.execute(
            update(UserModel).where(UserModel.id == user_id).values(token_version=UserModel.token_version + 1)
        )
        self._session.commit()
