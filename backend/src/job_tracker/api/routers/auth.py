from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response, status

from job_tracker.api.deps import (
    get_account_mailer,
    get_action_tokens,
    get_app_settings,
    get_current_user,
    get_email_throttle,
    get_login_throttle,
    get_offer_repository,
    get_quota_service,
    get_search_job_reader,
    get_search_profile_repository,
    get_user_repository,
)
from job_tracker.api.schemas.auth_schemas import (
    Credentials,
    ForgotPasswordRequest,
    LoginRequest,
    MessageOut,
    QuotaOut,
    ResetPasswordRequest,
    TokenOut,
    UserOut,
    VerifyEmailRequest,
)
from job_tracker.api.schemas.data_export_schemas import AccountExportOut, DeleteAccountRequest
from job_tracker.api.security.email_throttle import EmailThrottle
from job_tracker.api.security.login_throttle import LoginThrottle
from job_tracker.api.security.rate_limit import client_ip
from job_tracker.application.auth.account_data import DeleteAccount, ExportAccountData
from job_tracker.application.auth.accounts import AuthenticateUser, RegisterUser, normalize_email
from job_tracker.application.auth.mailer import AccountMailer
from job_tracker.application.auth.recovery import RequestPasswordReset, ResetPassword, VerifyEmail
from job_tracker.application.search.start_search import GetQuota
from job_tracker.config import Settings
from job_tracker.domain.candidate.search_profile_repository import SearchProfileRepository
from job_tracker.domain.offer.repository import OfferRepository
from job_tracker.domain.search.repository import SearchJobReader
from job_tracker.domain.user.entities import User
from job_tracker.domain.user.exceptions import InvalidCredentialsError, WrongPasswordError
from job_tracker.domain.user.repository import UserRepository
from job_tracker.domain.user.tokens import ActionTokens
from job_tracker.infrastructure.security.passwords import DUMMY_HASH, hash_password, verify_password
from job_tracker.infrastructure.security.tokens import create_access_token

# Rutas públicas (alta, login y enlaces del correo): las demás de /api exigen sesión.
public_router = APIRouter(prefix="/api/auth", tags=["auth"])
# Rutas de sesión: exigen token.
router = APIRouter(prefix="/api/auth", tags=["auth"], dependencies=[Depends(get_current_user)])

Users = Annotated[UserRepository, Depends(get_user_repository)]
AppSettings = Annotated[Settings, Depends(get_app_settings)]
Throttle = Annotated[LoginThrottle, Depends(get_login_throttle)]
EmailLimit = Annotated[EmailThrottle, Depends(get_email_throttle)]
Quotas = Annotated[GetQuota, Depends(get_quota_service)]
Tokens = Annotated[ActionTokens, Depends(get_action_tokens)]
Mailer = Annotated[AccountMailer, Depends(get_account_mailer)]
CurrentUser = Annotated[User, Depends(get_current_user)]

# Misma respuesta exista o no la cuenta: no se puede usar para averiguar qué emails están registrados.
_CHECK_YOUR_EMAIL = "Si el email es válido, te hemos enviado un mensaje. Revisa tu bandeja de entrada."


def _user_out(user: User, quotas: GetQuota) -> UserOut:
    quota = quotas.execute(user)
    return UserOut(
        email=user.email,
        plan=user.plan,
        email_verified=user.email_verified,
        quota=QuotaOut(limit=quota.limit, used=quota.used, remaining=quota.remaining),
    )


def _token(user: User, settings: Settings, quotas: GetQuota) -> TokenOut:
    secret = settings.jwt_secret.get_secret_value() if settings.jwt_secret else ""
    token = create_access_token(
        user.id or 0, secret=secret, minutes=settings.access_token_minutes, version=user.token_version
    )
    return TokenOut(access_token=token, user=_user_out(user, quotas))


@public_router.post("/register", response_model=MessageOut, status_code=status.HTTP_202_ACCEPTED)
def register(
    payload: Credentials,
    users: Users,
    settings: AppSettings,
    mailer: Mailer,
    email_limit: EmailLimit,
    background: BackgroundTasks,
) -> MessageOut:
    """Crea la cuenta y envía el correo de confirmación. No devuelve sesión ni dice si el email ya existía."""
    user = RegisterUser(users, hash_password, registration_open=settings.registration_open).execute(
        payload.email, payload.password
    )
    if email_limit.allow("register", payload.email):
        if user is not None:
            background.add_task(mailer.send_verification, user)
        else:
            background.add_task(mailer.send_already_registered, normalize_email(payload.email))
    return MessageOut(message=_CHECK_YOUR_EMAIL)


@public_router.post("/login", response_model=TokenOut)
def login(
    payload: LoginRequest, request: Request, users: Users, settings: AppSettings, quotas: Quotas, throttle: Throttle
) -> TokenOut:
    ip = client_ip(request.scope, trust_proxy=settings.trust_proxy)
    throttle.check(payload.email, ip)
    try:
        user = AuthenticateUser(users, verify_password, DUMMY_HASH).execute(payload.email, payload.password)
    except InvalidCredentialsError:
        throttle.record_failure(payload.email, ip)
        raise
    throttle.reset(payload.email, ip)
    return _token(user, settings, quotas)


@public_router.post("/verify-email", status_code=status.HTTP_204_NO_CONTENT)
def verify_email(payload: VerifyEmailRequest, users: Users, tokens: Tokens) -> Response:
    VerifyEmail(users, tokens).execute(payload.token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@public_router.post("/forgot-password", response_model=MessageOut, status_code=status.HTTP_202_ACCEPTED)
def forgot_password(
    payload: ForgotPasswordRequest,
    users: Users,
    mailer: Mailer,
    email_limit: EmailLimit,
    background: BackgroundTasks,
) -> MessageOut:
    user = RequestPasswordReset(users).execute(payload.email)
    if user is not None and email_limit.allow("reset", payload.email):
        background.add_task(mailer.send_password_reset, user)
    return MessageOut(message=_CHECK_YOUR_EMAIL)


@public_router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(payload: ResetPasswordRequest, users: Users, tokens: Tokens) -> Response:
    ResetPassword(users, tokens, hash_password).execute(payload.token, payload.password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser, quotas: Quotas) -> UserOut:
    return _user_out(user, quotas)


@router.post("/resend-verification", response_model=MessageOut, status_code=status.HTTP_202_ACCEPTED)
def resend_verification(
    user: CurrentUser, mailer: Mailer, email_limit: EmailLimit, background: BackgroundTasks
) -> MessageOut:
    if not user.email_verified and email_limit.allow("register", user.email):
        background.add_task(mailer.send_verification, user)
    return MessageOut(message=_CHECK_YOUR_EMAIL)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(user: CurrentUser, users: Users) -> Response:
    """Cierra la sesión en TODOS los dispositivos: invalida cualquier token emitido hasta ahora."""
    users.revoke_sessions(user.id or 0)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/export", response_model=AccountExportOut)
def export_account(
    user: CurrentUser,
    offers: Annotated[OfferRepository, Depends(get_offer_repository)],
    profiles: Annotated[SearchProfileRepository, Depends(get_search_profile_repository)],
    jobs: Annotated[SearchJobReader, Depends(get_search_job_reader)],
) -> AccountExportOut:
    """Todo lo que el servicio guarda de la persona (acceso y portabilidad). No incluye el hash de la contraseña."""
    return AccountExportOut.from_export(ExportAccountData(offers, profiles, jobs).execute(user))


@router.post("/delete-account", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    payload: DeleteAccountRequest,
    request: Request,
    user: CurrentUser,
    users: Users,
    settings: AppSettings,
    throttle: Throttle,
) -> Response:
    """Borra la cuenta y todos sus datos. Exige la contraseña y cuenta los fallos como un intento de login."""
    ip = client_ip(request.scope, trust_proxy=settings.trust_proxy)
    throttle.check(user.email, ip)
    try:
        DeleteAccount(users, verify_password).execute(user, payload.password)
    except WrongPasswordError:
        throttle.record_failure(user.email, ip)
        raise
    return Response(status_code=status.HTTP_204_NO_CONTENT)
