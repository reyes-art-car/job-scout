from datetime import UTC, date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from job_tracker.infrastructure.db.base import Base


def _utcnow() -> datetime:
    """UTC sin zona horaria (equivale al antiguo datetime.utcnow, ya obsoleto)."""
    return datetime.now(UTC).replace(tzinfo=None)


class OfferModel(Base):
    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    priority: Mapped[str] = mapped_column(String(20))
    compatibility: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(255))
    company: Mapped[str] = mapped_column(String(255))
    portal: Mapped[str] = mapped_column(String(255))
    url: Mapped[str | None] = mapped_column(String(1000), unique=True, nullable=True)
    published_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    location: Mapped[str] = mapped_column(String(255), default="")
    modality: Mapped[str] = mapped_column(String(100), default="")
    contract_type: Mapped[str] = mapped_column(String(100), default="No especificado")
    salary: Mapped[str | None] = mapped_column(String(255), nullable=True)
    experience_required: Mapped[str] = mapped_column(String(255), default="No especificado")
    mandatory_tech: Mapped[str] = mapped_column(Text, default="")
    desirable_tech: Mapped[str] = mapped_column(Text, default="")
    requirements_met: Mapped[str] = mapped_column(Text, default="")
    requirements_missing: Mapped[str] = mapped_column(Text, default="")
    score_reason: Mapped[str] = mapped_column(Text, default="")
    kanban_status: Mapped[str] = mapped_column(String(20), default="Pendiente")
    adapted_cv_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(30), default="document_upload")
    source_document_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    skills_order: Mapped[str] = mapped_column(String(30), default="backend_first")
    cv_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cv_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    bullets_order_csv: Mapped[str] = mapped_column(String(50), default="0,1,2,3,4,5")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class InterviewSessionModel(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mode: Mapped[str] = mapped_column(String(30))
    offer_id: Mapped[int | None] = mapped_column(ForeignKey("offers.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    messages: Mapped[list["ChatMessageModel"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="ChatMessageModel.id"
    )


class ChatMessageModel(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("interview_sessions.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(10))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    session: Mapped[InterviewSessionModel] = relationship(back_populates="messages")
