import os

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse

from job_tracker.api.deps import get_app_settings, get_offer_repository
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
from job_tracker.application.offer.list_offers import ListOffers
from job_tracker.application.offer.update_offer_status import UpdateOfferStatus
from job_tracker.config import Settings
from job_tracker.domain.offer.entities import KanbanStatus, Priority
from job_tracker.domain.offer.exceptions import DuplicateOfferError, OfferNotFoundError
from job_tracker.domain.offer.repository import OfferFilters, OfferRepository

router = APIRouter(prefix="/api/offers", tags=["offers"])


@router.get("", response_model=OfferListOut)
def list_offers(
    priority: Priority | None = None,
    status: KanbanStatus | None = None,
    min_compatibility: int | None = None,
    max_compatibility: int | None = None,
    portal: str | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 50,
    repository: OfferRepository = Depends(get_offer_repository),
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
    return OfferListOut(
        items=[OfferOut.from_entity(o) for o in offers], total=total, page=page, page_size=page_size
    )


@router.post("", response_model=OfferOut, status_code=201)
def create_offer(
    payload: OfferCreate, repository: OfferRepository = Depends(get_offer_repository)
) -> OfferOut:
    try:
        offer = CreateOffer(repository).execute(NewOfferData(**payload.model_dump()))
    except DuplicateOfferError as exc:
        raise HTTPException(status_code=409, detail="Ya existe una oferta con esa URL.") from exc
    return OfferOut.from_entity(offer)


@router.get("/export.csv")
def export_csv(repository: OfferRepository = Depends(get_offer_repository)) -> Response:
    offers, _ = ListOffers(repository).execute(OfferFilters(page=1, page_size=10_000))
    return Response(
        content=offers_to_csv(offers),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="ofertas.csv"'},
    )


@router.get("/stats", response_model=OfferStatsOut)
def get_stats(repository: OfferRepository = Depends(get_offer_repository)) -> OfferStatsOut:
    stats = ListOffers(repository).stats()
    return OfferStatsOut(total=stats.total, high_priority=stats.high_priority, by_status=stats.by_status)


@router.get("/{offer_id}", response_model=OfferOut)
def get_offer(
    offer_id: int, repository: OfferRepository = Depends(get_offer_repository)
) -> OfferOut:
    try:
        offer = GetOffer(repository).execute(offer_id)
    except OfferNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return OfferOut.from_entity(offer)


@router.patch("/{offer_id}/status", response_model=OfferOut)
def update_status(
    offer_id: int,
    payload: OfferStatusUpdate,
    repository: OfferRepository = Depends(get_offer_repository),
) -> OfferOut:
    try:
        offer = UpdateOfferStatus(repository).execute(offer_id, payload.status)
    except OfferNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return OfferOut.from_entity(offer)


@router.patch("/{offer_id}", response_model=OfferOut)
def patch_offer(
    offer_id: int,
    payload: OfferPatch,
    repository: OfferRepository = Depends(get_offer_repository),
) -> OfferOut:
    try:
        offer = GetOffer(repository).execute(offer_id)
    except OfferNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if payload.notes is not None:
        offer.notes = payload.notes
    if payload.salary is not None:
        offer.salary = payload.salary
    if payload.kanban_status is not None:
        offer.kanban_status = payload.kanban_status
    updated = repository.update(offer)
    return OfferOut.from_entity(updated)


@router.get("/{offer_id}/cv")
def download_cv(
    offer_id: int,
    repository: OfferRepository = Depends(get_offer_repository),
    settings: Settings = Depends(get_app_settings),
) -> FileResponse:
    try:
        offer = GetOffer(repository).execute(offer_id)
    except OfferNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if not offer.adapted_cv_filename:
        raise HTTPException(status_code=404, detail="Esta oferta no tiene un CV adaptado generado.")

    # El nombre del fichero viene de nuestra propia BD (nunca de un parámetro de
    # usuario), pero igualmente lo normalizamos con basename para evitar cualquier
    # posibilidad de path traversal antes de tocar el filesystem.
    safe_filename = os.path.basename(offer.adapted_cv_filename)
    cv_dir = os.path.abspath(str(settings.cv_output_dir))
    cv_path = os.path.abspath(os.path.join(cv_dir, safe_filename))
    if not cv_path.startswith(cv_dir + os.sep) or not os.path.isfile(cv_path):
        raise HTTPException(status_code=404, detail="El fichero de CV no existe en disco.")
    return FileResponse(cv_path, filename=safe_filename)
