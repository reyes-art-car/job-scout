from typing import Protocol

from job_tracker.domain.interview.entities import ChatMessage, InterviewSession


class InterviewRepository(Protocol):
    """Puerto del dominio para la persistencia de sesiones de entrevista."""

    def create_session(self, session: InterviewSession) -> InterviewSession: ...

    def get_session(self, session_id: int) -> InterviewSession | None:
        """Debe devolver la sesión con sus mensajes cargados (session.messages)."""
        ...

    def list_sessions(self) -> list[InterviewSession]: ...

    def add_message(self, message: ChatMessage) -> ChatMessage: ...
