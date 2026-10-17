from functools import lru_cache
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent

MIN_API_TOKEN_LENGTH = 32


class Settings(BaseSettings):
    """Configuración leída del entorno (`.env`). Nunca se versionan los valores reales."""

    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    app_env: Literal["development", "production"] = "development"

    # Autenticación: token Bearer estático (aplicación de un solo usuario). Obligatorio en producción.
    api_token: SecretStr | None = None

    anthropic_api_key: SecretStr = SecretStr("")
    anthropic_model: str = "claude-opus-5-5"

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

    legacy_excel_path: Path = BACKEND_DIR / ".." / "Ofertas_Maria_Reyes.xlsx"
    cv_output_dir: Path = BACKEND_DIR / ".." / "CV_adaptados"
    uploads_dir: Path = BACKEND_DIR / "data" / "uploads"
    candidate_profile_path: Path = BACKEND_DIR / "config" / "candidate_profile.yaml"
    knowledge_base_dir: Path = BACKEND_DIR / "knowledge_base"

    @field_validator("api_token", mode="before")
    @classmethod
    def _blank_token_means_none(cls, value: object) -> object:
        """`API_TOKEN=` vacío en el .env equivale a «sin token», nunca a un token vacío que cualquiera cumple."""
        return None if isinstance(value, str) and not value.strip() else value

    @model_validator(mode="after")
    def _reject_insecure_production(self) -> Self:
        if self.app_env != "production":
            return self
        token = self.api_token.get_secret_value() if self.api_token else ""
        if len(token) < MIN_API_TOKEN_LENGTH:
            raise ValueError(
                f"En producción API_TOKEN es obligatorio y debe tener al menos {MIN_API_TOKEN_LENGTH} caracteres."
            )
        if "*" in self.cors_origins_list:
            raise ValueError("CORS_ORIGINS no puede contener '*' en producción.")
        return self

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
