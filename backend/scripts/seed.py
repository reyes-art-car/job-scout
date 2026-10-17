"""Carga ofertas en la base de datos local.

    python scripts/seed.py --demo                         # data/demo/offers.json
    python scripts/seed.py --excel ../Ofertas_Maria_Reyes.xlsx

Ejecutar desde la carpeta backend/ con el entorno virtual activado.
"""

import argparse
from pathlib import Path

from job_tracker.config import get_settings
from job_tracker.infrastructure.db import models  # noqa: F401
from job_tracker.infrastructure.db.base import Base, SessionLocal, engine
from job_tracker.infrastructure.db.sqlalchemy_offer_repository import SqlAlchemyOfferRepository
from job_tracker.infrastructure.excel_import.importer import import_demo_json, import_excel

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--demo", action="store_true", help="importa data/demo/offers.json")
    source.add_argument("--excel", type=Path, help="importa un Excel con el formato de busqueda_diaria.py")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        repository = SqlAlchemyOfferRepository(session)
        if args.demo:
            report = import_demo_json(REPO_ROOT / "data" / "demo" / "offers.json", repository)
        else:
            report = import_excel((args.excel or get_settings().legacy_excel_path).resolve(), repository)
    print(
        f"Importadas: {report.imported} · duplicadas: {report.skipped_duplicates}"
        f" · inválidas: {report.skipped_invalid}"
    )


if __name__ == "__main__":
    main()
