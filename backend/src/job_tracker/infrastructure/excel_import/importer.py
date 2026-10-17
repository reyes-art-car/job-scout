"""Importadores de ofertas: Excel histórico (Ofertas_*.xlsx) y JSON de demostración."""

import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import openpyxl

from job_tracker.domain.offer.entities import KanbanStatus, Offer, OfferSource, Priority
from job_tracker.domain.offer.repository import OfferRepository


@dataclass
class ImportReport:
    imported: int = 0
    skipped_duplicates: int = 0
    skipped_invalid: int = 0


def _status(raw: object) -> KanbanStatus:
    text = str(raw or "").lower()
    if "entrev" in text:
        return KanbanStatus.ENTREVISTA
    if "rechaz" in text or "descart" in text:
        return KanbanStatus.RECHAZO
    if "ofert" in text and "pendiente" not in text:
        return KanbanStatus.OFERTA
    if "aplic" in text or "enviad" in text:
        return KanbanStatus.APLICADO
    return KanbanStatus.PENDIENTE


def _compat(raw: object) -> int:
    match = re.search(r"\d+", str(raw or ""))
    return min(int(match.group()), 100) if match else 0


def _date(raw: object) -> date | None:
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    try:
        return date.fromisoformat(str(raw)[:10])
    except ValueError:
        return None


def _priority(raw: object, compatibility: int) -> Priority:
    if str(raw).strip().lower() == "alta":
        return Priority.ALTA
    if str(raw).strip().lower() == "secundaria":
        return Priority.SECUNDARIA
    return Priority.ALTA if compatibility >= 75 else Priority.SECUNDARIA


def _str(raw: object, default: str = "") -> str:
    return default if raw is None else str(raw).strip()


def import_excel(path: Path, repository: OfferRepository) -> ImportReport:
    """Importa filas del Excel con las 21 columnas de busqueda_diaria.py, sin duplicar por ID o URL."""
    report = ImportReport()
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        sheet = workbook.active
        for row in sheet.iter_rows(min_row=2, values_only=True):
            code, title, company = _str(row[0]), _str(row[3]), _str(row[4])
            if not (code and title and company):
                report.skipped_invalid += 1
                continue
            url = _str(row[6]) or None
            if repository.exists_by_code_or_url(code, url):
                report.skipped_duplicates += 1
                continue
            compatibility = _compat(row[2])
            repository.add(
                Offer(
                    id=None,
                    code=code,
                    priority=_priority(row[1], compatibility),
                    compatibility=compatibility,
                    title=title,
                    company=company,
                    portal=_str(row[5]),
                    url=url,
                    published_date=_date(row[7]),
                    location=_str(row[8]),
                    modality=_str(row[9]),
                    contract_type=_str(row[10], "No especificado"),
                    salary=_str(row[11]) or None,
                    experience_required=_str(row[12], "No especificado"),
                    mandatory_tech=_str(row[13]),
                    desirable_tech=_str(row[14]),
                    requirements_met=_str(row[15]),
                    requirements_missing=_str(row[16]),
                    score_reason=_str(row[17]),
                    kanban_status=_status(row[18]),
                    adapted_cv_filename=_str(row[19]) or None if len(row) > 19 else None,
                    notes=_str(row[20]) or None if len(row) > 20 else None,
                    source=OfferSource.LEGACY_EXCEL,
                )
            )
            report.imported += 1
    finally:
        workbook.close()
    return report


def import_demo_json(path: Path, repository: OfferRepository) -> ImportReport:
    """Carga data/demo/offers.json (mismo formato que devuelve la API)."""
    report = ImportReport()
    for item in json.loads(path.read_text(encoding="utf-8")):
        url = item.get("url") or None
        if repository.exists_by_code_or_url(item["code"], url):
            report.skipped_duplicates += 1
            continue
        compatibility = int(item["compatibility"])
        repository.add(
            Offer(
                id=None,
                code=item["code"],
                priority=_priority(item.get("priority"), compatibility),
                compatibility=compatibility,
                title=item["title"],
                company=item["company"],
                portal=item.get("portal", ""),
                url=url,
                published_date=_date(item.get("published_date")),
                location=item.get("location", ""),
                modality=item.get("modality", ""),
                contract_type=item.get("contract_type", "No especificado"),
                salary=item.get("salary") or None,
                experience_required=item.get("experience_required", "No especificado"),
                mandatory_tech=item.get("mandatory_tech", ""),
                desirable_tech=item.get("desirable_tech", ""),
                requirements_met=item.get("requirements_met", ""),
                requirements_missing=item.get("requirements_missing", ""),
                score_reason=item.get("score_reason", ""),
                kanban_status=KanbanStatus(item.get("kanban_status", "Pendiente")),
                adapted_cv_filename=None,
                notes=item.get("notes"),
                source=OfferSource(item.get("source", "legacy_excel")),
            )
        )
        report.imported += 1
    return report
