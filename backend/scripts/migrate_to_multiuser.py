"""Migra una base de datos SQLite de un solo usuario (esquema anterior) al esquema multiusuario.

    python scripts/migrate_to_multiuser.py --email tu@correo.com

Todas las ofertas y sesiones de entrevista existentes pasan a ser de esa cuenta (se crea si no existe).
Hace una copia de seguridad `<base>.bak` antes de tocar nada y no hace nada si la base ya está migrada.
Solo SQLite: en Postgres se parte de una base nueva y se importan las ofertas con seed.py.
"""

import argparse
import getpass
import os
import shutil
import sqlite3
from pathlib import Path

from sqlalchemy import make_url

from job_tracker.config import get_settings
from job_tracker.infrastructure.security.passwords import hash_password

MIN_PASSWORD_LENGTH = 10
LEGACY_TABLES = ("offers", "interview_sessions")


def _db_path() -> Path:
    url = make_url(get_settings().database_url)
    if url.get_backend_name() != "sqlite" or not url.database:
        raise SystemExit("Este script solo migra bases SQLite.")
    return Path(url.database).resolve()


def _columns(con: sqlite3.Connection, table: str) -> list[str]:
    return [row[1] for row in con.execute(f"PRAGMA table_info({table})")]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--email", required=True)
    email = parser.parse_args().email.strip().lower()

    path = _db_path()
    if not path.exists():
        raise SystemExit(f"No existe la base de datos {path}")
    with sqlite3.connect(path) as probe:
        offer_columns = _columns(probe, "offers")
    if not offer_columns:
        print("La base de datos no tiene ofertas del esquema anterior. Se creará con el esquema nuevo al arrancar.")
        return
    if "user_id" in offer_columns:
        print("La base de datos ya está en el esquema multiusuario. Nada que hacer.")
        return

    password = os.environ.get("SEED_PASSWORD") or getpass.getpass(f"Contraseña para {email}: ")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise SystemExit(f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres.")
    backup = path.with_suffix(path.suffix + ".bak")
    shutil.copy2(path, backup)

    try:
        _migrate(path, email, password)
    except Exception:
        shutil.copy2(backup, path)  # una migración a medias es peor que ninguna: se restaura la copia
        print(f"La migración falló y se ha restaurado la base original desde {backup}.")
        raise
    print(f"Migrado. Las ofertas existentes pertenecen ahora a {email}. Copia de seguridad en {backup}")


def _migrate(path: Path, email: str, password: str) -> None:
    # Importar el módulo de modelos registra las tablas nuevas en Base.metadata.
    from job_tracker.infrastructure.db import models  # noqa: F401, PLC0415
    from job_tracker.infrastructure.db.base import Base  # noqa: PLC0415

    con = sqlite3.connect(path)
    try:
        con.execute("PRAGMA foreign_keys = OFF")
        # Sin esto, renombrar una tabla reescribe las claves foráneas de las demás para apuntar a «_old».
        con.execute("PRAGMA legacy_alter_table = ON")
        old_columns = {table: _columns(con, table) for table in LEGACY_TABLES if _columns(con, table)}
        for table in old_columns:
            con.execute(f"ALTER TABLE {table} RENAME TO {table}_old")
        # Los índices conservan su nombre al renombrar la tabla y chocarían con los nuevos.
        for table in old_columns:
            rows = con.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL AND tbl_name = ?",
                (f"{table}_old",),
            ).fetchall()
            for (index,) in rows:
                con.execute(f'DROP INDEX IF EXISTS "{index}"')
        con.commit()

        from sqlalchemy import create_engine  # noqa: PLC0415

        engine = create_engine(f"sqlite:///{path}")
        Base.metadata.create_all(bind=engine)
        engine.dispose()

        con.execute(
            "INSERT INTO users (email, password_hash, plan, created_at) VALUES (?, ?, 'free', datetime('now'))",
            (email, hash_password(password)),
        )
        user_id = con.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()[0]
        for table, columns in old_columns.items():
            names = ", ".join(columns)
            con.execute(f"INSERT INTO {table} (user_id, {names}) SELECT ?, {names} FROM {table}_old", (user_id,))  # noqa: S608
            con.execute(f"DROP TABLE {table}_old")
        con.commit()
    finally:
        con.close()


if __name__ == "__main__":
    main()
