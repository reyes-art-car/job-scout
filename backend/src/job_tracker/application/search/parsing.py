"""Extrae y valida las ofertas que devuelve el modelo.

La respuesta del LLM es entrada NO confiable: el anuncio que lee puede contener instrucciones
(«prompt injection») y el modelo puede equivocarse. Nada de lo que devuelve se guarda sin pasar por aquí.
"""

import json
import re
from datetime import date
from typing import Any

from job_tracker.application.offer.create_offer import NewOfferData
from job_tracker.domain.offer.entities import OfferSource
from job_tracker.shared.sanitize import clean_bounded, validate_http_url

_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)
MAX_RESPONSE_CHARS = 2_000_000
MAX_OFFERS = 200
MIN_COMPATIBILITY = 60  # el prompt pide descartar por debajo, pero no se confía en que el modelo lo cumpla
SHORT, LONG = 255, 4000


class InvalidOfferError(ValueError):
    """La oferta no cumple el mínimo para guardarse (título, empresa y URL http/https válidos)."""


def extract_offer_dicts(response: str) -> list[dict[str, Any]]:
    """Extrae el primer array JSON de objetos de la respuesta (con o sin bloque ```json).

    Se decodifica con `raw_decode` desde cada «[»: tolera texto antes y después y no depende de
    expresiones regulares que fallen con llaves anidadas. Devuelve [] si no hay un array válido.
    """
    text = response[:MAX_RESPONSE_CHARS]
    candidates = [match.group(1) for match in _FENCE.finditer(text)] + [text]
    decoder = json.JSONDecoder()
    for candidate in candidates:
        for start in (i for i, char in enumerate(candidate) if char == "["):
            try:
                value, _ = decoder.raw_decode(candidate[start:])
            except json.JSONDecodeError:
                continue
            if isinstance(value, list) and all(isinstance(item, dict) for item in value):
                return value[:MAX_OFFERS]
    return []


def _text(raw: dict[str, Any], key: str, default: str = "", limit: int = SHORT) -> str:
    value = raw.get(key)
    return clean_bounded(str(value), limit) if value not in (None, "") else default


def _compatibility(raw: Any) -> int:
    try:
        value = int(float(str(raw).rstrip("% ")))
    except (TypeError, ValueError):
        return 0
    return max(0, min(100, value))


def _date(raw: Any) -> date | None:
    try:
        return date.fromisoformat(str(raw)[:10])
    except ValueError:
        return None


def parse_found_offer(raw: Any) -> NewOfferData:
    """Convierte un dict del modelo en datos de oferta seguros o lanza `InvalidOfferError`."""
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
    if compatibility < MIN_COMPATIBILITY:
        raise InvalidOfferError("compatibilidad por debajo del mínimo")

    salary = _text(raw, "salary")
    return NewOfferData(
        title=title,
        company=company,
        portal=_text(raw, "portal", "Otro"),
        url=url,
        published_date=_date(raw.get("date")),
        location=_text(raw, "location"),
        modality=_text(raw, "modality"),
        contract_type=_text(raw, "contract", "No especificado"),
        salary=salary or None,
        experience_required=_text(raw, "experience", "No especificado"),
        mandatory_tech=_text(raw, "mandatory_tech", limit=LONG),
        desirable_tech=_text(raw, "desirable_tech", limit=LONG),
        requirements_met=_text(raw, "meets", limit=LONG),
        requirements_missing=_text(raw, "missing", limit=LONG),
        score_reason=_text(raw, "score_reason", limit=LONG),
        compatibility=compatibility,
        notes=_text(raw, "notes", limit=LONG) or None,
        source=OfferSource.CLAUDE_AGENT_SEARCH,
    )
