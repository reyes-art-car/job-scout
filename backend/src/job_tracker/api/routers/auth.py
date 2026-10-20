from typing import Annotated

from fastapi import APIRouter, Depends, status

from job_tracker.api.deps import get_app_settings, get_current_user, get_quota_service, get_user_repository
from job_tracker.api.schemas.account_schemas import Credentials, LoginRequest, QuotaOut, TokenOut, UserOut
from job_tracker.application.auth.accounts import AuthenticateUser, RegisterUser
from job_tracker.application.search.start_search import GetQuota
from job_tracker.config import Settings
from job_tracker.domain.user.entities import User
from job_tracker.domain.user.repository import UserRepository
from job_tracker.infrastructure.security.passwords import DUMMY_HASH, hash_password, verify_password
from job_tracker.infrastructure.security.tokens import create_access_token

# Rutas públicas (registro y login): las demás de /api exigen token.
public_router = APIRouter(prefix="/api/auth", tags=["auth"])
# Rutas de sesión: exigen token.
router = APIRouter(prefix="/api/auth", tags=["auth"], dependencies=[Depends(get_current_user)])

Users = Annotated[UserRepository, Depends(get_user_repository)]
Settings_ = Annotated[Settings, Depends(get_app_settings)]
Quotas = Annotated[GetQuota, Depends(get_quota_service)]


def _user_out(user: User, quotas: GetQuota) -> UserOut:
    quota = quotas.execute(user)
    return UserOut(
        email=user.email,
        plan=user.plan,
        quota=QuotaOut(limit=quota.limit, used=quota.used, remaining=quota.remaining),
    )


def _token(user: User, settings: Settings, quotas: GetQuota) -> TokenOut:
    secret = settings.jwt_secret.get_secret_value() if settings.jwt_secret else ""
    token = create_access_token(user.id or 0, secret=secret, minutes=settings.access_token_minutes)
    return TokenOut(access_token=token, user=_user_out(user, quotas))


@public_router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(payload: Credentials, users: Users, settings: Settings_, quotas: Quotas) -> TokenOut:
    user = RegisterUser(users, hash_password, registration_open=settings.registration_open).execute(
        payload.email, payload.password
    )
    return _token(user, settings, quotas)


@public_router.post("/login", response_model=TokenOut)
def login(payload: LoginRequest, users: Users, settings: Settings_, quotas: Quotas) -> TokenOut:
    user = AuthenticateUser(users, verify_password, DUMMY_HASH).execute(payload.email, payload.password)
    return _token(user, settings, quotas)


@router.get("/me", response_model=UserOut)
def me(user: Annotated[User, Depends(get_current_user)], quotas: Quotas) -> UserOut:
    return _user_out(user, quotas)
