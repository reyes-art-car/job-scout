from datetime import UTC, date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from job_tracker.infrastructure.db.base import Base


def _utcnow() -> datetime:
    """UTC sin zona horaria (equivale al antiguo datetime.utcnow, ya obsoleto)."""
    return datetime.now(UTC).replace(tzinfo=None)


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    plan: Mapped[str] = mapped_column(String(20), default="free")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class SearchProfileModel(Base):
    __tablename__ = "search_profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    data: Mapped[str] = mapped_column(Text)  # JSON validado en la API
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class SearchJobModel(Base):
    __tablename__ = "search_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    strategy: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(10), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    offers_added: Mapped[int] = mapped_column(Integer, default=0)
    offers_skipped: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    web_searches: Mapped[int] = mapped_column(Integer, default=0)
    web_fetches: Mapped[int] = mapped_column(Integer, default=0)


class OfferModel(Base):
    __tablename__ = "offers"
    # El código (OF001…) y la URL son únicos por usuario, no globales: dos usuarios pueden ver la misma oferta.
    __table_args__ = (
        UniqueConstraint("user_id", "code", name="uq_offers_user_code"),
        UniqueConstraint("user_id", "url", name="uq_offers_user_url"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(String(16), index=True)
    priority: Mapped[str] = mapped_column(String(20))
    compatibility: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(255))
    company: Mapped[str] = mapped_column(String(255))
    portal: Mapped[str] = mapped_column(String(255))
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
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
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
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
