from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from job_tracker.domain.interview.entities import ChatMessage, ChatRole, GuidedMode, InterviewSession
from job_tracker.infrastructure.db.models import ChatMessageModel, InterviewSessionModel


def _message_to_entity(row: ChatMessageModel) -> ChatMessage:
    return ChatMessage(
        id=row.id,
        session_id=row.session_id,
        role=ChatRole(row.role),
        content=row.content,
        created_at=row.created_at,
    )


def _session_to_entity(row: InterviewSessionModel) -> InterviewSession:
    return InterviewSession(
        id=row.id,
        mode=GuidedMode(row.mode),
        offer_id=row.offer_id,
        title=row.title,
        created_at=row.created_at,
        messages=[_message_to_entity(m) for m in row.messages],
    )


class SqlAlchemyInterviewRepository:
    """Adaptador de infraestructura: implementa el puerto InterviewRepository."""

    def __init__(self, session: Session):
        self._session = session

    def create_session(self, session: InterviewSession) -> InterviewSession:
        row = InterviewSessionModel(
            mode=session.mode.value, offer_id=session.offer_id, title=session.title
        )
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return _session_to_entity(row)

    def get_session(self, session_id: int) -> InterviewSession | None:
        stmt = (
            select(InterviewSessionModel)
            .options(selectinload(InterviewSessionModel.messages))
            .where(InterviewSessionModel.id == session_id)
        )
        row = self._session.scalar(stmt)
        return _session_to_entity(row) if row else None

    def list_sessions(self) -> list[InterviewSession]:
        stmt = select(InterviewSessionModel).options(
            selectinload(InterviewSessionModel.messages)
        ).order_by(InterviewSessionModel.created_at.desc())
        rows = self._session.scalars(stmt).all()
        return [_session_to_entity(r) for r in rows]

    def add_message(self, message: ChatMessage) -> ChatMessage:
        row = ChatMessageModel(
            session_id=message.session_id, role=message.role.value, content=message.content
        )
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return _message_to_entity(row)
