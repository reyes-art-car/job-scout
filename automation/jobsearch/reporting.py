import datetime
from collections.abc import Sequence
from pathlib import Path

from .offer import JobOffer


def write_log(
    log_dir: Path,
    today: datetime.date,
    offers: Sequence[JobOffer],
    skipped: int,
    label: str | None = None,
    now: datetime.datetime | None = None,
) -> Path:
    """Añade un bloque al log del día (sin sobrescribir si ya hubo otra ejecución hoy)."""
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / f"busqueda_{today:%Y%m%d}.txt"
    is_new = not path.exists()
    stamp = (now or datetime.datetime.now(tz=datetime.UTC)).strftime("%H:%M:%S")
    lines: list[str] = []
    if is_new:
        lines += [f"Busqueda diaria — {today:%d/%m/%Y}", "=" * 60, ""]
    else:
        lines += ["", "-" * 60, ""]
    lines += [
        f"Ejecucion {stamp}" + (f" ({label})" if label else ""),
        f"Ofertas nuevas encontradas: {len(offers)}",
        f"Ofertas descartadas (duplicadas o excluidas): {skipped}",
        "",
    ]
    for offer in offers:
        lines += [f"[{offer.id}] {offer.compatibility}% — {offer.title} @ {offer.company}", f"        {offer.url}", ""]
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    return path
