import datetime
import logging
from collections.abc import Callable

from job_tracker.application.offer.create_offer import CreateOffer
from job_tracker.application.search.parsing import InvalidOfferError, extract_offer_dicts, parse_found_offer
from job_tracker.application.search.prompt import MAX_KNOWN_URLS, STRATEGIES, build_search_prompt
from job_tracker.domain.candidate.search_profile_repository import SearchProfileRepository
from job_tracker.domain.offer.exceptions import DuplicateOfferError
from job_tracker.domain.offer.repository import OfferRepository
from job_tracker.domain.search.entities import SearchJob, SearchStatus
from job_tracker.domain.search.exceptions import LlmError
from job_tracker.domain.search.llm import SearchLlm
from job_tracker.domain.search.repository import SearchJobQueue
from job_tracker.shared.clock import utc_now

logger = logging.getLogger("job_tracker.search")

OfferRepositoryFactory = Callable[[int], OfferRepository]


class RunSearchJob:
    """Ejecuta un trabajo ya reclamado: perfil → prompt → modelo → validación → ofertas del usuario.

    Nunca lanza: cualquier fallo deja el trabajo en «fallido» con un mensaje seguro para el usuario
    (el detalle técnico va al log) y sin descontar cupo.
    """

    def __init__(
        self,
        queue: SearchJobQueue,
        profiles: SearchProfileRepository,
        offers_for_user: OfferRepositoryFactory,
        llm: SearchLlm,
    ):
        self._queue = queue
        self._profiles = profiles
        self._offers_for_user = offers_for_user
        self._llm = llm

    def execute(self, job: SearchJob, today: datetime.date | None = None) -> SearchJob:
        try:
            return self._run(job, today or utc_now().date())
        except LlmError as exc:
            return self._fail(job, str(exc))
        except Exception:
            logger.exception("Error inesperado en la búsqueda %s", job.id)
            return self._fail(job, "Error interno al ejecutar la búsqueda. Inténtalo de nuevo más tarde.")

    def _run(self, job: SearchJob, today: datetime.date) -> SearchJob:
        profile = self._profiles.get(job.user_id)
        if profile is None:
            return self._fail(job, "Completa tu perfil de búsqueda antes de buscar.")

        offers = self._offers_for_user(job.user_id)
        prompt = build_search_prompt(
            profile=profile, known_urls=offers.known_urls(MAX_KNOWN_URLS), today=today, strategy=job.strategy
        )
        result = self._llm.search(prompt)
        job.input_tokens, job.output_tokens = result.input_tokens, result.output_tokens
        job.web_searches, job.web_fetches = result.web_searches, result.web_fetches

        creator = CreateOffer(offers)
        added = skipped = 0
        for raw in extract_offer_dicts(result.text):
            if added >= STRATEGIES[job.strategy].max_offers:
                break
            try:
                creator.execute(parse_found_offer(raw))
                added += 1
            except (InvalidOfferError, DuplicateOfferError) as exc:
                logger.info("Oferta descartada: %s", exc)
                skipped += 1

        job.offers_added, job.offers_skipped = added, skipped
        job.status = SearchStatus.DONE
        job.finished_at = utc_now()
        return self._queue.save(job)

    def _fail(self, job: SearchJob, message: str) -> SearchJob:
        job.status = SearchStatus.FAILED
        job.error = message[:500]
        job.finished_at = utc_now()
        return self._queue.save(job)
