import re
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, StringConstraints

from job_tracker.domain.user.entities import Plan

MIN_PASSWORD_LENGTH = 10
MAX_PASSWORD_LENGTH = 128  # evita que una contraseña enorme se use para agotar CPU en el hash
_EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,189}\.[^@\s.]{2,}$")


def _validate_email(value: str) -> str:
    email = value.strip().lower()
    if not _EMAIL.fullmatch(email):
        raise ValueError("Email no válido")
    return email


Email = Annotated[str, StringConstraints(max_length=254), AfterValidator(_validate_email)]
Password = Annotated[str, StringConstraints(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)]


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: Email
    password: Password


class LoginRequest(BaseModel):
    """En el login no se valida la longitud mínima: la política solo se aplica al crear la contraseña."""

    model_config = ConfigDict(extra="forbid")

    email: Email
    password: Annotated[str, StringConstraints(min_length=1, max_length=MAX_PASSWORD_LENGTH)]


ActionToken = Annotated[str, StringConstraints(min_length=10, max_length=2000)]


class VerifyEmailRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: ActionToken


class ForgotPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: Email


class ResetPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: ActionToken
    password: Password


class MessageOut(BaseModel):
    message: str


class QuotaOut(BaseModel):
    limit: int
    used: int
    remaining: int


class UserOut(BaseModel):
    email: str
    plan: Plan
    email_verified: bool
    quota: QuotaOut


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105
    user: UserOut
