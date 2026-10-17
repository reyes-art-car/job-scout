from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import FileResponse

from job_tracker.api.deps import (
    get_cv_locator,
    get_offer_repository,
)
from job_tracker.api.schemas.offer_schemas import (
    OfferCreate,
    OfferListOut,
    OfferOut,
    OfferPatch,
    OfferStatsOut,
    OfferStatusUpdate,
)
from job_tracker.application.offer.create_offer import CreateOffer, NewOfferData
from job_tracker.application.offer.export_offers import offers_to_csv
from job_tracker.application.offer.get_offer import GetOffer
from job_tracker.application.offer.get_offer_cv import CvLocator, GetOfferCv
from job_tracker.application.offer.list_offers import GetOfferStats, ListOffers
from job_tracker.application.offer.update_offer import OfferChanges, UpdateOffer
from job_tracker.application.offer.update_offer_status import UpdateOfferStatus
from job_tracker.domain.offer.entities import KanbanStatus, Priority
from job_tracker.domain.offer.repository import OfferFilters, OfferRepository

router = APIRouter(prefix="/api/offers", tags=["offers"])

MAX_PAGE_SIZE = 500
EXPORT_LIMIT = 10_000

Repository = Annotated[OfferRepository, Depends(get_offer_repository)]
Locator = Annotated[CvLocator, Depends(get_cv_locator)]


@router.get("", response_model=OfferListOut)
def list_offers(
    repository: Repository,
    priority: Priority | None = None,
    status: KanbanStatus | None = None,
    min_compatibility: Annotated[int | None, Query(ge=0, le=100)] = None,
    max_compatibility: Annotated[int | None, Query(ge=0, le=100)] = None,
    portal: Annotated[str | None, Query(max_length=100)] = None,
    search: Annotated[str | None, Query(max_length=100)] = None,
    page: Annotated[int, Query(ge=1, le=10_000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = 50,
) -> OfferListOut:
    filters = OfferFilters(
        priority=priority,
        kanban_status=status,
        min_compatibility=min_compatibility,
        max_compatibility=max_compatibility,
        portal=portal,
        search=search,
        page=page,
        page_size=page_size,
    )
    offers, total = ListOffers(repository).execute(filters)
    return OfferListOut(items=[OfferOut.from_entity(o) for o in offers], total=total, page=page, page_size=page_size)


@router.post("", response_model=OfferOut, status_code=201)
def create_offer(payload: OfferCreate, repository: Repository) -> OfferOut:
    offer = CreateOffer(repository).execute(NewOfferData(**payload.model_dump()))
    return OfferOut.from_entity(offer)


@router.get("/export.csv")
def export_csv(repository: Repository) -> Response:
    offers, _ = ListOffers(repository).execute(OfferFilters(page=1, page_size=EXPORT_LIMIT))
    return Response(
        content=offers_to_csv(offers),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="ofertas.csv"'},
    )


@router.get("/stats", response_model=OfferStatsOut)
def get_stats(repository: Repository) -> OfferStatsOut:
    stats = GetOfferStats(repository).execute()
    return OfferStatsOut(total=stats.total, high_priority=stats.high_priority, by_status=stats.by_status)


@router.get("/{offer_id}", response_model=OfferOut)
def get_offer(offer_id: int, repository: Repository) -> OfferOut:
    return OfferOut.from_entity(GetOffer(repository).execute(offer_id))


@router.patch("/{offer_id}/status", response_model=OfferOut)
def update_status(offer_id: int, payload: OfferStatusUpdate, repository: Repository) -> OfferOut:
    return OfferOut.from_entity(UpdateOfferStatus(repository).execute(offer_id, payload.status))


@router.patch("/{offer_id}", response_model=OfferOut)
def patch_offer(offer_id: int, payload: OfferPatch, repository: Repository) -> OfferOut:
    changes = OfferChanges(notes=payload.notes, salary=payload.salary, kanban_status=payload.kanban_status)
    return OfferOut.from_entity(UpdateOffer(repository).execute(offer_id, changes))


@router.get("/{offer_id}/cv")
def download_cv(offer_id: int, repository: Repository, locator: Locator) -> FileResponse:
    path = GetOfferCv(repository, locator).execute(offer_id)
    return FileResponse(path, filename=path.name)
