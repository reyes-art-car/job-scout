from job_tracker.domain.user.entities import User
from job_tracker.domain.user.exceptions import InvalidActionTokenError
from job_tracker.domain.user.tokens import ActionKind
from job_tracker.infrastructure.security.tokens import (
    RESET_LINK,
    VERIFY_EMAIL,
    InvalidTokenError,
    create_action_token,
    decode_action_token,
)

_TYPES = {ActionKind.VERIFY_EMAIL: VERIFY_EMAIL, ActionKind.RESET: RESET_LINK}


class JwtActionTokens:
    def __init__(self, *, secret: str, verify_hours: int, reset_minutes: int) -> None:
        self._secret = secret
        self._minutes = {ActionKind.VERIFY_EMAIL: verify_hours * 60, ActionKind.RESET: reset_minutes}

    def issue(self, kind: ActionKind, user: User) -> str:
        return create_action_token(
            _TYPES[kind], user.id or 0, secret=self._secret, minutes=self._minutes[kind], version=user.token_version
        )

    def read(self, kind: ActionKind, token: str) -> tuple[int, int]:
        try:
            claims = decode_action_token(token, _TYPES[kind], secret=self._secret)
        except InvalidTokenError as exc:
            raise InvalidActionTokenError from exc
        return claims.user_id, claims.version
