"""Oferta devuelta por el modelo, validada y saneada.

La respuesta del LLM es entrada NO confiable: el anuncio que lee puede contener instrucciones
(«prompt injection») y el modelo puede equivocarse. Nada de lo que devuelve llega al Excel, al
sistema de ficheros ni a un documento sin pasar por aquí.
"""

import re
from dataclasses import dataclass, field, replace
from typing import Any

from job_tracker.shared.sanitize import clean_bounded, validate_http_url

from .config import SKILLS_ORDERS

PRIORITIES = ("Alta", "Secundaria")
HIGH_PRIORITY_MIN = 75
CV_MIN_COMPATIBILITY = 65
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SAFE_FILENAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}\.docx$")
_FILENAME_JUNK = re.compile(r"[^A-Za-z0-9]+")

SHORT, LONG = 255, 4000


class InvalidOfferError(ValueError):
    """La oferta no cumple el mínimo para guardarse (título, empresa o URL http/https válidos)."""


@dataclass
class JobOffer:
    id: str
    compatibility: int
    priority: str
    title: str
    company: str
    url: str
    portal: str = ""
    date: str = ""
    location: str = ""
    modality: str = ""
    contract: str = "No especificado"
    salary: str = "No especificado"
    experience: str = "No especificado"
    mandatory_tech: str = ""
    desirable_tech: str = ""
    meets: str = ""
    missing: str = ""
    score_reason: str = ""
    status: str = "Pendiente de revisión"
    notes: str = ""
    cv_file: str | None = None
    cv_title: str = ""
    cv_summary: str = ""
    cv_skills_order: str = "fullstack"
    cv_bullets: list[int] = field(default_factory=list)

    @property
    def wants_cv(self) -> bool:
        return self.cv_file is not None and self.compatibility >= CV_MIN_COMPATIBILITY

    def with_sequence_number(self, number: int) -> "JobOffer":
        """Reasigna el ID secuencial (el del modelo no es de fiar) y lo refleja en el nombre del CV."""
        new_id = f"OF{number:03d}"
        cv_file = self.cv_file
        if cv_file is not None:
            cv_file = f"{new_id}_{cv_file.split('_', 1)[1]}" if "_" in cv_file else cv_file
        return replace(self, id=new_id, cv_file=cv_file)


def _text(raw: dict[str, Any], key: str, default: str = "", limit: int = SHORT) -> str:
    value = raw.get(key)
    return clean_bounded(str(value), limit) if value not in (None, "") else default


def safe_cv_filename(candidate: str | None, fallback_parts: tuple[str, ...]) -> str | None:
    """Nombre de .docx seguro: solo letras, números, _ . - y sin rutas. Un nombre malicioso se descarta
    y se sustituye por uno generado a partir de `fallback_parts` (ID, empresa, puesto)."""
    if candidate:
        name = candidate.strip()
        if _SAFE_FILENAME.fullmatch(name) and ".." not in name:
            return name
    cleaned = [_FILENAME_JUNK.sub("", part)[:30] for part in fallback_parts]
    stem = "_".join(part for part in cleaned if part)
    return f"{stem}.docx" if stem else None


def _bullets(raw: Any, count: int) -> list[int]:
    if not isinstance(raw, list):
        return []
    seen: list[int] = []
    for item in raw:
        if isinstance(item, int) and not isinstance(item, bool) and 0 <= item < count and item not in seen:
            seen.append(item)
    return seen


def _compatibility(raw: Any) -> int:
    try:
        value = int(float(str(raw).rstrip("% ")))
    except (TypeError, ValueError):
        return 0
    return max(0, min(100, value))


def parse_offer(raw: Any, *, bullet_count: int) -> JobOffer:
    """Convierte un dict del modelo en una `JobOffer` segura o lanza `InvalidOfferError`."""
    if not isinstance(raw, dict):
        raise InvalidOfferError("la oferta no es un objeto")
    title, company = _text(raw, "title"), _text(raw, "company")
    if not title or not company:
        raise InvalidOfferError("falta título o empresa")
    try:
        url = validate_http_url(str(raw.get("url", ""))[:1000])
    except ValueError as exc:
        raise InvalidOfferError("URL no válida (solo http/https)") from exc

    compatibility = _compatibility(raw.get("compatibility"))
    priority = _text(raw, "priority")
    if priority not in PRIORITIES:
        priority = "Alta" if compatibility >= HIGH_PRIORITY_MIN else "Secundaria"
    date = _text(raw, "date")
    skills_order = _text(raw, "cv_skills_order")

    offer = JobOffer(
        id=_text(raw, "id", "OF000", 16),
        compatibility=compatibility,
        priority=priority,
        title=title,
        company=company,
        url=url,
        portal=_text(raw, "portal"),
        date=date if _DATE.fullmatch(date) else "",
        location=_text(raw, "location"),
        modality=_text(raw, "modality"),
        contract=_text(raw, "contract", "No especificado"),
        salary=_text(raw, "salary", "No especificado"),
        experience=_text(raw, "experience", "No especificado"),
        mandatory_tech=_text(raw, "mandatory_tech", limit=LONG),
        desirable_tech=_text(raw, "desirable_tech", limit=LONG),
        meets=_text(raw, "meets", limit=LONG),
        missing=_text(raw, "missing", limit=LONG),
        score_reason=_text(raw, "score_reason", limit=LONG),
        status="Pendiente de revisión",  # lo decide la aplicación, no el modelo
        notes=_text(raw, "notes", limit=LONG),
        cv_title=_text(raw, "cv_title"),
        cv_summary=_text(raw, "cv_summary", limit=LONG),
        cv_skills_order=skills_order if skills_order in SKILLS_ORDERS else "fullstack",
        cv_bullets=_bullets(raw.get("cv_bullets"), bullet_count),
    )
    if raw.get("cv_file"):
        offer.cv_file = safe_cv_filename(str(raw["cv_file"]), (offer.id, company, title))
    return offer
