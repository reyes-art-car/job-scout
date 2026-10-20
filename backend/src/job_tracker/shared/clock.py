from datetime import UTC, datetime


def utc_now() -> datetime:
    """Ahora en UTC sin zona horaria: es lo que guarda la base de datos (equivale al antiguo utcnow)."""
    return datetime.now(UTC).replace(tzinfo=None)
