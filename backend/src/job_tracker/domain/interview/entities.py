from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class GuidedMode(str, Enum):
    TECHNICAL_QUESTION = "technical_question"
    BEHAVIORAL_STAR = "behavioral_star"
    MOCK_INTERVIEW = "mock_interview"
    GENERAL_TIPS = "general_tips"


class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class ChatMessage:
    id: int | None
    session_id: int
    role: ChatRole
    content: str
    created_at: datetime | None = None


@dataclass
class InterviewSession:
    id: int | None
    mode: GuidedMode
    offer_id: int | None
    title: str
    created_at: datetime | None = None
    messages: list[ChatMessage] | None = None
