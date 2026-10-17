import csv
import io
from collections.abc import Iterable

from job_tracker.domain.offer.entities import Offer

# Mismas columnas y orden que Ofertas_Maria_Reyes.xlsx y que el exportador del frontend.
COLUMNS: list[tuple[str, str]] = [
    ("ID", "code"),
    ("Prioridad", "priority"),
    ("% Compatibilidad", "compatibility"),
    ("Puesto", "title"),
    ("Empresa", "company"),
    ("Portal", "portal"),
    ("Enlace", "url"),
    ("Fecha publicación", "published_date"),
    ("Ubicación", "location"),
    ("Modalidad", "modality"),
    ("Tipo contrato", "contract_type"),
    ("Salario", "salary"),
    ("Experiencia solicitada", "experience_required"),
    ("Tecnologías obligatorias", "mandatory_tech"),
    ("Tecnologías deseables", "desirable_tech"),
    ("Requisitos que cumplo", "requirements_met"),
    ("Requisitos que NO cumplo", "requirements_missing"),
    ("Motivo puntuación", "score_reason"),
    ("Estado candidatura", "kanban_status"),
    ("Observaciones", "notes"),
]


def _cell(offer: Offer, attr: str) -> str:
    value = getattr(offer, attr)
    if value is None:
        return ""
    if attr == "compatibility":
        return f"{value}%"
    text = value.value if hasattr(value, "value") else str(value)
    # Evita la inyección de fórmulas al abrir el CSV en Excel.
    return f"'{text}" if text[:1] in ("=", "+", "-", "@") else text


def offers_to_csv(offers: Iterable[Offer]) -> str:
    """CSV con «;» y BOM UTF-8: Excel en español lo abre con columnas y acentos correctos."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", quoting=csv.QUOTE_ALL, lineterminator="\r\n")
    writer.writerow([header for header, _ in COLUMNS])
    for offer in offers:
        writer.writerow([_cell(offer, attr) for _, attr in COLUMNS])
    return "﻿" + buffer.getvalue()
