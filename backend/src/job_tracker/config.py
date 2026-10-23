import secrets
from functools import lru_cache
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent

MIN_JWT_SECRET_LENGTH = 32


class Settings(BaseSettings):
    """Configuración leída del entorno (`.env`). Nunca se versionan los valores reales."""

    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    app_env: Literal["development", "production"] = "development"

    # Cuentas de usuario: JWT firmado con este secreto. Obligatorio en producción; en desarrollo, si falta,
    # se genera uno aleatorio al arrancar (las sesiones dejan de valer al reiniciar).
    jwt_secret: SecretStr | None = None
    access_token_minutes: int = Field(default=720, gt=0)
    registration_open: bool = True
    # Vida de los enlaces enviados por correo. El de restablecer contraseña es corto a propósito.
    verify_link_hours: int = Field(default=48, gt=0)
    reset_link_minutes: int = Field(default=30, gt=0)
    # Correos de cuenta (confirmación, restablecer clave) por dirección y hora: evita inundar el buzón de un tercero.
    emails_per_address_per_hour: int = Field(default=3, gt=0)
    # Dirección pública del frontend, para construir los enlaces de los correos.
    app_base_url: str = "http://localhost:4200"

    # Correo saliente. «console» solo en desarrollo (escribe el correo en el log); producción exige SMTP.
    email_backend: Literal["console", "smtp"] = "console"
    smtp_host: str = ""
    smtp_port: int = Field(default=587, gt=0)
    smtp_security: Literal["starttls", "ssl", "none"] = "starttls"
    smtp_username: str = ""
    smtp_password: SecretStr = SecretStr("")
    email_from: str = ""

    anthropic_api_key: SecretStr = SecretStr("")
    anthropic_model: str = "claude-opus-5-5"

    # Búsqueda de ofertas con la API de Claude. El modelo de búsqueda es independiente del resto.
    search_model: str = "claude-sonnet-5-5"
    search_max_tokens: int = Field(default=16_000, gt=0)
    search_max_web_searches: int = Field(default=20, gt=0)
    search_max_web_fetches: int = Field(default=20, gt=0)
    search_timeout_seconds: int = Field(default=900, gt=0)
    worker_poll_seconds: float = Field(default=5.0, gt=0)
    # Un trabajo «en curso» más antiguo que esto se da por muerto (el worker se cayó) y se marca como fallido.
    stale_job_minutes: int = Field(default=30, gt=0)

    # Búsquedas incluidas por mes natural según el plan. La pasarela de pago (futuro) solo cambia el plan.
    # Freno global de coste: máximo de búsquedas aceptadas en 24 h entre TODOS los usuarios. Evita que
    # muchas cuentas gratuitas recién creadas agoten el presupuesto de la API de Claude.
    max_searches_per_day: int = Field(default=200, gt=0)
    free_searches_per_month: int = Field(default=1, ge=0)
    pro_searches_per_month: int = Field(default=30, ge=0)

    database_url: str = "sqlite:///./job_tracker.db"
    cors_origins: str = "http://localhost:4200"
    allowed_hosts: str = "localhost,127.0.0.1,testserver"

    # Detrás de un proxy inverso (nginx), la IP real llega en X-Forwarded-For: solo se confía si se activa.
    trust_proxy: bool = False
    enable_docs: bool | None = None  # None → solo en desarrollo

    max_body_bytes: int = Field(default=1_048_576, gt=0)
    rate_limit_per_minute: int = Field(default=120, gt=0)
    rate_limit_writes_per_minute: int = Field(default=30, gt=0)
    rate_limit_exports_per_minute: int = Field(default=6, gt=0)
    rate_limit_auth_per_minute: int = Field(default=10, gt=0)
    # Intentos de login fallidos por cuenta antes de bloquearla temporalmente (además del límite por IP).
    login_failures_per_window: int = Field(default=10, gt=0)
    login_window_minutes: int = Field(default=15, gt=0)

    legacy_excel_path: Path = BACKEND_DIR / ".." / "Ofertas_Maria_Reyes.xlsx"
    cv_output_dir: Path = BACKEND_DIR / ".." / "CV_adaptados"
    uploads_dir: Path = BACKEND_DIR / "data" / "uploads"
    candidate_profile_path: Path = BACKEND_DIR / "config" / "candidate_profile.yaml"
    knowledge_base_dir: Path = BACKEND_DIR / "knowledge_base"

    @field_validator("jwt_secret", mode="before")
    @classmethod
    def _blank_secret_means_none(cls, value: object) -> object:
        """`JWT_SECRET=` vacío en el .env equivale a «sin secreto», nunca a un secreto vacío que cualquiera cumple."""
        return None if isinstance(value, str) and not value.strip() else value

    @model_validator(mode="after")
    def _reject_insecure_production(self) -> Self:
        if self.app_env != "production":
            if self.jwt_secret is None:
                self.jwt_secret = SecretStr(secrets.token_urlsafe(48))
            return self
        secret = self.jwt_secret.get_secret_value() if self.jwt_secret else ""
        if len(secret) < MIN_JWT_SECRET_LENGTH:
            raise ValueError(
                f"En producción JWT_SECRET es obligatorio y debe tener al menos {MIN_JWT_SECRET_LENGTH} caracteres."
            )
        if not self.anthropic_api_key.get_secret_value():
            raise ValueError("En producción ANTHROPIC_API_KEY es obligatoria (la búsqueda usa la API de Claude).")
        if self.email_backend != "smtp" or not self.smtp_host or not self.email_from:
            raise ValueError("En producción EMAIL_BACKEND=smtp, SMTP_HOST y EMAIL_FROM son obligatorios.")
        if not self.app_base_url.startswith("https://"):
            raise ValueError("En producción APP_BASE_URL debe ser https:// (los correos llevan enlaces con tokens).")
        if "*" in self.cors_origins_list:
            raise ValueError("CORS_ORIGINS no puede contener '*' en producción.")
        return self

    def searches_per_month(self, plan: str) -> int:
        return self.pro_searches_per_month if plan == "pro" else self.free_searches_per_month

    @property
    def docs_enabled(self) -> bool:
        return self.enable_docs if self.enable_docs is not None else self.app_env == "development"

    @property
    def resolved_candidate_profile_path(self) -> Path:
        """El perfil real (con datos de contacto) no se versiona: si falta, se usa la plantilla."""
        if self.candidate_profile_path.exists():
            return self.candidate_profile_path
        return self.candidate_profile_path.with_name("candidate_profile.example.yaml")

    @property
    def cors_origins_list(self) -> list[str]:
        return _split_csv(self.cors_origins)

    @property
    def allowed_hosts_list(self) -> list[str]:
        return _split_csv(self.allowed_hosts)


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
