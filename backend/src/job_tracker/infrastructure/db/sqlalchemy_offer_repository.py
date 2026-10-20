from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from job_tracker.domain.offer.entities import KanbanStatus, Offer, OfferSource, Priority
from job_tracker.domain.offer.exceptions import OfferNotFoundError
from job_tracker.domain.offer.repository import OfferFilters, OfferStats
from job_tracker.infrastructure.db.models import OfferModel

_LIKE_ESCAPE = "\\"


def _contains(term: str) -> str:
    """Patrón LIKE «contiene» con los comodines (%, _) del texto del usuario escapados."""
    escaped = term.replace(_LIKE_ESCAPE, _LIKE_ESCAPE * 2)
    for wildcard in ("%", "_"):
        escaped = escaped.replace(wildcard, _LIKE_ESCAPE + wildcard)
    return f"%{escaped}%"


def _to_entity(row: OfferModel) -> Offer:
    return Offer(
        id=row.id,
        code=row.code,
        priority=Priority(row.priority),
        compatibility=row.compatibility,
        title=row.title,
        company=row.company,
        portal=row.portal,
        url=row.url,
        published_date=row.published_date,
        location=row.location,
        modality=row.modality,
        contract_type=row.contract_type,
        salary=row.salary,
        experience_required=row.experience_required,
        mandatory_tech=row.mandatory_tech,
        desirable_tech=row.desirable_tech,
        requirements_met=row.requirements_met,
        requirements_missing=row.requirements_missing,
        score_reason=row.score_reason,
        kanban_status=KanbanStatus(row.kanban_status),
        adapted_cv_filename=row.adapted_cv_filename,
        notes=row.notes,
        source=OfferSource(row.source),
        source_document_filename=row.source_document_filename,
        raw_extracted_text=row.raw_extracted_text,
        created_at=row.created_at,
        updated_at=row.updated_at,
        extra_bullets_order=[int(i) for i in row.bullets_order_csv.split(",") if i.strip() != ""],
        skills_order=row.skills_order,
        cv_title=row.cv_title,
        cv_summary=row.cv_summary,
    )


def _apply_entity_to_row(offer: Offer, row: OfferModel) -> None:
    row.code = offer.code
    row.priority = offer.priority.value
    row.compatibility = offer.compatibility
    row.title = offer.title
    row.company = offer.company
    row.portal = offer.portal
    row.url = offer.url
    row.published_date = offer.published_date
    row.location = offer.location
    row.modality = offer.modality
    row.contract_type = offer.contract_type
    row.salary = offer.salary
    row.experience_required = offer.experience_required
    row.mandatory_tech = offer.mandatory_tech
    row.desirable_tech = offer.desirable_tech
    row.requirements_met = offer.requirements_met
    row.requirements_missing = offer.requirements_missing
    row.score_reason = offer.score_reason
    row.kanban_status = offer.kanban_status.value
    row.adapted_cv_filename = offer.adapted_cv_filename
    row.notes = offer.notes
    row.source = offer.source.value
    row.source_document_filename = offer.source_document_filename
    row.raw_extracted_text = offer.raw_extracted_text
    row.skills_order = offer.skills_order
    row.cv_title = offer.cv_title
    row.cv_summary = offer.cv_summary
    row.bullets_order_csv = ",".join(str(i) for i in offer.extra_bullets_order)


class SqlAlchemyOfferRepository:
    """Adaptador de infraestructura: implementa el puerto OfferRepository con SQLAlchemy.

    Está acotado a un usuario: todas las consultas filtran por `user_id` y una fila ajena se trata
    como inexistente, de modo que ningún caso de uso puede ver ni modificar ofertas de otra persona.
    """

    def __init__(self, session: Session, user_id: int):
        self._session = session
        self._user_id = user_id

    def _own(self, row: OfferModel | None) -> OfferModel | None:
        return row if row is not None and row.user_id == self._user_id else None

    def known_urls(self, limit: int) -> list[str]:
        stmt = (
            select(OfferModel.url)
            .where(OfferModel.user_id == self._user_id, OfferModel.url.is_not(None))
            .order_by(OfferModel.id.desc())
            .limit(limit)
        )
        return [url for url in self._session.scalars(stmt) if url]

    def list(self, filters: OfferFilters) -> tuple[list[Offer], int]:
        stmt = select(OfferModel).where(OfferModel.user_id == self._user_id)
        if filters.priority is not None:
            stmt = stmt.where(OfferModel.priority == filters.priority.value)
        if filters.kanban_status is not None:
            stmt = stmt.where(OfferModel.kanban_status == filters.kanban_status.value)
        if filters.min_compatibility is not None:
            stmt = stmt.where(OfferModel.compatibility >= filters.min_compatibility)
        if filters.max_compatibility is not None:
            stmt = stmt.where(OfferModel.compatibility <= filters.max_compatibility)
        if filters.portal:
            stmt = stmt.where(OfferModel.portal.ilike(_contains(filters.portal), escape=_LIKE_ESCAPE))
        if filters.search:
            like = _contains(filters.search)
            stmt = stmt.where(
                or_(
                    OfferModel.title.ilike(like, escape=_LIKE_ESCAPE),
                    OfferModel.company.ilike(like, escape=_LIKE_ESCAPE),
                )
            )

        total = self._session.scalar(select(func.count()).select_from(stmt.subquery())) or 0

        stmt = (
            stmt.order_by(OfferModel.compatibility.desc(), OfferModel.id.desc())
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
        )
        rows = self._session.scalars(stmt).all()
        return [_to_entity(r) for r in rows], total

    def get(self, offer_id: int) -> Offer | None:
        row = self._own(self._session.get(OfferModel, offer_id))
        return _to_entity(row) if row else None

    def get_by_code(self, code: str) -> Offer | None:
        row = self._session.scalar(
            select(OfferModel).where(OfferModel.user_id == self._user_id, OfferModel.code == code)
        )
        return _to_entity(row) if row else None

    def exists_by_code_or_url(self, code: str, url: str | None) -> bool:
        match = OfferModel.code == code
        if url:
            match = or_(match, OfferModel.url == url)
        stmt = select(OfferModel.id).where(OfferModel.user_id == self._user_id, match)
        return self._session.scalar(stmt) is not None

    def add(self, offer: Offer) -> Offer:
        row = OfferModel(user_id=self._user_id)
        _apply_entity_to_row(offer, row)
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return _to_entity(row)

    def update(self, offer: Offer) -> Offer:
        row = self._own(self._session.get(OfferModel, offer.id))
        if row is None:
            raise OfferNotFoundError(offer.id or -1)
        _apply_entity_to_row(offer, row)
        self._session.commit()
        self._session.refresh(row)
        return _to_entity(row)

    def update_status(self, offer_id: int, status: KanbanStatus) -> Offer:
        row = self._own(self._session.get(OfferModel, offer_id))
        if row is None:
            raise OfferNotFoundError(offer_id)
        row.kanban_status = status.value
        self._session.commit()
        self._session.refresh(row)
        return _to_entity(row)

    def next_code(self) -> str:
        codes = self._session.scalars(select(OfferModel.code).where(OfferModel.user_id == self._user_id)).all()
        last_num = 0
        for code in codes:
            try:
                last_num = max(last_num, int(code.replace("OF", "")))
            except ValueError:
                continue
        return f"OF{last_num + 1:03d}"

    def stats(self) -> OfferStats:
        mine = OfferModel.user_id == self._user_id
        total = self._session.scalar(select(func.count()).select_from(OfferModel).where(mine)) or 0
        high_priority = (
            self._session.scalar(
                select(func.count()).select_from(OfferModel).where(mine, OfferModel.priority == Priority.ALTA.value)
            )
            or 0
        )
        rows = self._session.execute(
            select(OfferModel.kanban_status, func.count()).where(mine).group_by(OfferModel.kanban_status)
        ).all()
        by_status = {status: count for status, count in rows}  # noqa: C416  (Row no es una tupla simple)
        return OfferStats(total=total, high_priority=high_priority, by_status=by_status)
