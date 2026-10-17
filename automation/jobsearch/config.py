"""Rutas y perfil de la candidata. Sin efectos secundarios al importar: todo se construye bajo demanda."""

from dataclasses import dataclass
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Colores del CV (docx) y del Excel
HDR_TEAL = "1A6870"
XL_TEAL = "006666"
XL_LIGHT = "E8F4F4"

# Columnas del Excel (mismo orden que backend/application/offer/export_offers.py)
EXCEL_COLUMNS = [
    "ID", "Prioridad", "% Compatibilidad", "Puesto", "Empresa", "Portal", "Enlace",
    "Fecha publicación", "Ubicación", "Modalidad", "Tipo contrato", "Salario",
    "Experiencia solicitada", "Tecnologías obligatorias", "Tecnologías deseables",
    "Requisitos que cumplo", "Requisitos que NO cumplo", "Motivo puntuación",
    "Estado candidatura", "Nombre CV adaptado", "Observaciones",
]  # fmt: skip

SKILLS_ORDERS = ("backend_first", "fullstack", "frontend_first")


@dataclass(frozen=True)
class Paths:
    base: Path
    cv_dir: Path
    excel: Path
    log_dir: Path

    @classmethod
    def for_project(cls, base: Path = PROJECT_ROOT) -> "Paths":
        return cls(
            base=base,
            cv_dir=base / "CV_adaptados",
            excel=base / "Ofertas_Maria_Reyes.xlsx",
            log_dir=base / "logs",
        )


@dataclass(frozen=True)
class SkillGroup:
    label: str
    content: str


@dataclass(frozen=True)
class Profile:
    name: str
    contact_line: str
    bullets: list[str]
    skills: dict[str, list[SkillGroup]]
    prompt_block: str


def load_profile(base: Path = PROJECT_ROOT) -> Profile:
    """Lee backend/config/candidate_profile.yaml (datos reales, fuera de git) o, si falta, la plantilla."""
    config_dir = base / "backend" / "config"
    path = next(
        p for p in (config_dir / "candidate_profile.yaml", config_dir / "candidate_profile.example.yaml") if p.exists()
    )
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return Profile(
        name=data["name"],
        contact_line=data["contact_line"],
        bullets=list(data["bullets"]),
        skills={
            order: [SkillGroup(g["label"], g["content"]) for g in groups] for order, groups in data["skills"].items()
        },
        prompt_block=data["summary_prompt_block"],
    )
