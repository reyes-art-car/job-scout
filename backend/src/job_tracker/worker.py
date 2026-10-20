"""Worker de búsquedas: proceso aparte que consume la cola de la base de datos.

    python -m job_tracker.worker            # bucle continuo
    python -m job_tracker.worker --once     # procesa lo que haya en cola y termina (útil para pruebas)

Se ejecuta como servicio (systemd) junto a la API. La API solo encola; aquí es donde se llama a la API de
Claude, de modo que una búsqueda lenta nunca bloquea las peticiones web.
"""

import argparse
import logging
import time
from collections.abc import Callable
from datetime import timedelta

from sqlalchemy.orm import Session

from job_tracker.application.search.run_search_job import RunSearchJob
from job_tracker.config import Settings, get_settings
from job_tracker.domain.search.llm import SearchLlm
from job_tracker.infrastructure.db.base import SessionLocal
from job_tracker.infrastructure.db.sqlalchemy_offer_repository import SqlAlchemyOfferRepository
from job_tracker.infrastructure.db.sqlalchemy_search_job_repository import SqlAlchemySearchJobRepository
from job_tracker.infrastructure.db.sqlalchemy_search_profile_repository import SqlAlchemySearchProfileRepository
from job_tracker.infrastructure.llm.anthropic_search import AnthropicSearchLlm
from job_tracker.shared.clock import utc_now

logger = logging.getLogger("job_tracker.worker")


def build_llm(settings: Settings) -> SearchLlm:
    return AnthropicSearchLlm(
        api_key=settings.anthropic_api_key.get_secret_value(),
        model=settings.search_model,
        max_tokens=settings.search_max_tokens,
        max_web_searches=settings.search_max_web_searches,
        max_web_fetches=settings.search_max_web_fetches,
        timeout_seconds=settings.search_timeout_seconds,
    )


def process_next(session: Session, llm: SearchLlm) -> bool:
    """Reclama y ejecuta un trabajo. Devuelve False si no había ninguno en cola."""
    jobs = SqlAlchemySearchJobRepository(session)
    job = jobs.claim_next()
    if job is None:
        return False
    logger.info("Búsqueda %s (usuario %s, %s) en curso", job.id, job.user_id, job.strategy)
    done = RunSearchJob(
        queue=jobs,
        profiles=SqlAlchemySearchProfileRepository(session),
        offers_for_user=lambda user_id: SqlAlchemyOfferRepository(session, user_id),
        llm=llm,
    ).execute(job)
    logger.info(
        "Búsqueda %s: %s · +%d ofertas · %d tokens entrada / %d salida · %d búsquedas web",
        done.id,
        done.status.value,
        done.offers_added,
        done.input_tokens,
        done.output_tokens,
        done.web_searches,
    )
    return True


def run(settings: Settings, session_factory: Callable[[], Session] = SessionLocal, *, once: bool = False) -> None:
    llm = build_llm(settings)
    while True:
        with session_factory() as session:
            stale = SqlAlchemySearchJobRepository(session).fail_stale(
                utc_now() - timedelta(minutes=settings.stale_job_minutes)
            )
            if stale:
                logger.warning("%d búsquedas interrumpidas marcadas como fallidas", stale)
            busy = process_next(session, llm)
        if once and not busy:
            return
        if not busy:
            time.sleep(settings.worker_poll_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--once", action="store_true", help="procesa la cola y termina")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    run(get_settings(), once=args.once)


if __name__ == "__main__":
    main()
