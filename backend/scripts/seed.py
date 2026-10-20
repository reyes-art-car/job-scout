"""Carga ofertas en la cuenta de un usuario (la crea si no existe).

    python scripts/seed.py --email tu@correo.com --demo
    python scripts/seed.py --email tu@correo.com --excel ../Ofertas_Maria_Reyes.xlsx

La contraseña de una cuenta nueva se pide por consola (o se lee de SEED_PASSWORD).
Ejecutar desde la carpeta backend/ con el entorno virtual activado.
"""

import argparse
import getpass
import os
from pathlib import Path

from job_tracker.application.auth.accounts import RegisterUser, normalize_email
from job_tracker.config import get_settings
from job_tracker.domain.user.entities import User
from job_tracker.infrastructure.db import models  # noqa: F401
from job_tracker.infrastructure.db.base import Base, SessionLocal, engine
from job_tracker.infrastructure.db.sqlalchemy_offer_repository import SqlAlchemyOfferRepository
from job_tracker.infrastructure.db.sqlalchemy_user_repository import SqlAlchemyUserRepository
from job_tracker.infrastructure.excel_import.importer import import_demo_json, import_excel
from job_tracker.infrastructure.security.passwords import hash_password

REPO_ROOT = Path(__file__).resolve().parents[2]
MIN_PASSWORD_LENGTH = 10


def _get_or_create_user(users: SqlAlchemyUserRepository, email: str) -> User:
    existing = users.get_by_email(normalize_email(email))
    if existing is not None:
        return existing
    password = os.environ.get("SEED_PASSWORD") or getpass.getpass(f"Contraseña para la cuenta nueva {email}: ")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise SystemExit(f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres.")
    return RegisterUser(users, hash_password, registration_open=True).execute(email, password)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--email", required=True, help="cuenta que recibirá las ofertas")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--demo", action="store_true", help="importa data/demo/offers.json")
    source.add_argument("--excel", type=Path, help="importa un Excel con el formato de busqueda_diaria.py")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        user = _get_or_create_user(SqlAlchemyUserRepository(session), args.email)
        repository = SqlAlchemyOfferRepository(session, user.id or 0)
        if args.demo:
            report = import_demo_json(REPO_ROOT / "data" / "demo" / "offers.json", repository)
        else:
            report = import_excel((args.excel or get_settings().legacy_excel_path).resolve(), repository)
    print(
        f"Importadas: {report.imported} · duplicadas: {report.skipped_duplicates} · inválidas: {report.skipped_invalid}"
    )


if __name__ == "__main__":
    main()
