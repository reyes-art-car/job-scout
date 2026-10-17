from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-5-5"

    database_url: str = "sqlite:///./job_tracker.db"
    cors_origins: str = "http://localhost:4200"

    legacy_excel_path: Path = BACKEND_DIR / ".." / "Ofertas_Maria_Reyes.xlsx"
    cv_output_dir: Path = BACKEND_DIR / ".." / "CV_adaptados"
    uploads_dir: Path = BACKEND_DIR / "data" / "uploads"
    candidate_profile_path: Path = BACKEND_DIR / "config" / "candidate_profile.yaml"
    knowledge_base_dir: Path = BACKEND_DIR / "knowledge_base"

    @property
    def resolved_candidate_profile_path(self) -> Path:
        """El perfil real (con datos de contacto) no se versiona: si falta, se usa la plantilla."""
        if self.candidate_profile_path.exists():
            return self.candidate_profile_path
        return self.candidate_profile_path.with_name("candidate_profile.example.yaml")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
