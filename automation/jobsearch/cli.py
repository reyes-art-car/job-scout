"""Orquestación de la búsqueda diaria y punto de entrada de línea de comandos."""

import argparse
import datetime
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from .config import Paths, Profile, load_profile
from .cv_docx import CvDocumentBuilder
from .excel_store import OfferWorkbook
from .llm import ClaudeCodeCli, LlmClient, LlmError
from .offer import InvalidOfferError, JobOffer, parse_offer
from .parsing import extract_offer_dicts
from .prompt import STRATEGIES, build_search_prompt
from .reporting import write_log

logger = logging.getLogger("jobsearch")


@dataclass
class RunReport:
    new_offers: list[JobOffer]
    skipped: int
    cvs_created: list[Path]
    log_path: Path


def run_search(
    *,
    paths: Paths,
    profile: Profile,
    llm: LlmClient,
    today: datetime.date,
    strategy: str = "general",
) -> RunReport:
    """Una ejecución completa: prompt → modelo → validación → Excel → CVs → log. Todas las dependencias se inyectan."""
    workbook = OfferWorkbook(paths.excel)
    known_urls, last_id = workbook.known_urls_and_last_id()
    logger.info("URLs ya conocidas: %d · último ID: OF%03d", len(known_urls), last_id)

    prompt = build_search_prompt(
        candidate_profile=profile.prompt_block, known_urls=known_urls, last_id=last_id, today=today, strategy=strategy
    )
    raw_items = extract_offer_dicts(llm.complete(prompt))
    logger.info("El modelo devolvió %d ofertas candidatas", len(raw_items))

    new_offers: list[JobOffer] = []
    skipped = 0
    next_number = last_id + 1
    for raw in raw_items:
        try:
            offer = parse_offer(raw, bullet_count=len(profile.bullets))
        except InvalidOfferError as exc:
            logger.warning("Oferta descartada: %s", exc)
            skipped += 1
            continue
        if offer.url in known_urls:
            skipped += 1
            continue
        known_urls.add(offer.url)
        new_offers.append(offer.with_sequence_number(next_number))
        next_number += 1

    label = STRATEGIES[strategy].label
    if not new_offers:
        return RunReport([], skipped, [], write_log(paths.log_dir, today, [], skipped, label))

    workbook.append(new_offers)
    builder = CvDocumentBuilder(profile, paths.cv_dir)
    cvs: list[Path] = []
    for offer in new_offers:
        if not offer.wants_cv:
            continue
        try:
            cvs.append(builder.build(offer))
        except (ValueError, OSError, IndexError) as exc:
            logger.warning("No se pudo generar el CV de %s: %s", offer.id, exc)
    return RunReport(new_offers, skipped, cvs, write_log(paths.log_dir, today, new_offers, skipped, label))


def _print_summary(report: RunReport, paths: Paths, today: datetime.date) -> None:
    print("\n" + "=" * 60)
    print(f"RESUMEN {today:%d/%m/%Y}")
    print(f"  Nuevas ofertas añadidas al Excel : {len(report.new_offers)}")
    print(f"  CVs adaptados generados          : {len(report.cvs_created)}")
    print(f"  Excel                            : {paths.excel}")
    print(f"  CVs en                           : {paths.cv_dir}")
    print("=" * 60)
    top = sorted(report.new_offers, key=lambda o: o.compatibility, reverse=True)[:10]
    if top:
        print("\nTop ofertas de hoy:")
        print(f"{'ID':<7} {'%':<5} {'Empresa':<22} {'Puesto':<35} Modalidad")
        print("-" * 95)
        for o in top:
            print(f"{o.id:<7} {o.compatibility:<5} {o.company[:20]:<22} {o.title[:33]:<35} {o.modality[:20]}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Búsqueda diaria de ofertas junior Java/Spring/Angular con Claude Code"
    )
    parser.add_argument(
        "--portal",
        choices=[name for name in STRATEGIES if name != "general"],
        help="linkedin: solo LinkedIn España · europa: empresas internacionales 100%% remoto",
    )
    args = parser.parse_args(argv)
    strategy = args.portal or "general"

    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    today = datetime.datetime.now(tz=datetime.UTC).astimezone().date()
    label = STRATEGIES[strategy].label
    print(f"\nBusqueda diaria — {today:%d/%m/%Y}" + (f" ({label})" if label else ""))
    print("=" * 60)

    paths = Paths.for_project()
    try:
        report = run_search(paths=paths, profile=load_profile(), llm=ClaudeCodeCli(), today=today, strategy=strategy)
    except LlmError as exc:
        logger.error("%s", exc)
        return 1
    if not report.new_offers:
        print("[INFO] No hay nuevas ofertas para añadir hoy.")
        return 0
    _print_summary(report, paths, today)
    return 0
