from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...database import SessionLocal
from ...domain.enums import MediaType
from ...integrations import ExternalSearchResult, ShikimoriAdapter
from ...models import RatingProfile
from ...services.dev_user import get_dev_user
from ...services.external_import import import_shikimori_rates
from ...services.external_titles import ensure_external_source, link_external_title
from ...services.library_entries import add_to_list, get_entry, get_user_lists, update_entry
from ...services.title_search import search_titles
from ...services.titles import create_title
from ...services.user_ratings import save_user_rating

router = APIRouter(prefix="/ratings", tags=["ratings"])
title_search_router = APIRouter(tags=["titles"])


class TitleCreatePayload(BaseModel):
    title: str
    media_type: MediaType


def get_session():
    with SessionLocal() as session:
        yield session


class RatingPayload(BaseModel):
    user_id: int | None
    title_id: int
    media_type: MediaType
    criteria_values: dict[str, int] = Field(min_length=1)


@router.put("", response_model=dict)
def upsert_rating(payload: RatingPayload, session: Session = Depends(get_session)):
    if payload.user_id is None:
        payload.user_id = get_dev_user(session).id
    profile = session.scalar(
        select(RatingProfile)
        .where(
            RatingProfile.user_id == payload.user_id,
            RatingProfile.media_type == payload.media_type,
        )
        .order_by(RatingProfile.version.desc())
    )
    if profile is None:
        profile = session.scalar(
            select(RatingProfile)
            .where(
                RatingProfile.user_id.is_(None),
                RatingProfile.media_type == payload.media_type,
                RatingProfile.is_default.is_(True),
            )
            .order_by(RatingProfile.version.desc())
        )
    if profile is None:
        raise HTTPException(status_code=400, detail="Rating profile not found.")
    try:
        rating = save_user_rating(
            session,
            user_id=payload.user_id,
            title_id=payload.title_id,
            criteria_values=payload.criteria_values,
            profile=profile,
        )
        session.commit()
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "id": rating.id,
        "overall_rating": rating.overall_rating,
        "criteria_values": rating.criteria_values,
        "rating_profile_version": rating.rating_profile_version,
    }


@title_search_router.post("/titles", response_model=dict, status_code=201)
def create_title_endpoint(
    payload: TitleCreatePayload,
    session: Session = Depends(get_session),
):
    try:
        title = create_title(
            session,
            title=payload.title,
            media_type=payload.media_type,
        )
        session.commit()
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "id": title.id,
        "title": title.title,
        "media_type": title.media_type,
    }


@title_search_router.get("/lists", response_model=list[dict])
def get_lists_endpoint(
    user_id: int,
    media_type: MediaType,
    session: Session = Depends(get_session),
):
    if user_id is None:
        user_id = get_dev_user(session).id
        session.commit()
    return [
        {"id": item.id, "name": item.name, "is_system": item.is_system}
        for item in get_user_lists(session, user_id=user_id, media_type=media_type)
    ]


class LibraryEntryPayload(BaseModel):
    user_id: int | None
    title_id: int
    list_id: int


@title_search_router.post("/library", response_model=dict, status_code=201)
def add_to_list_endpoint(
    payload: LibraryEntryPayload,
    session: Session = Depends(get_session),
):
    if payload.user_id is None:
        payload.user_id = get_dev_user(session).id
    try:
        entry = add_to_list(
            session,
            user_id=payload.user_id,
            title_id=payload.title_id,
            list_id=payload.list_id,
        )
        session.commit()
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"id": entry.id, "title_id": entry.title_id, "list_id": entry.list_id}


@title_search_router.get("/titles/search", response_model=list[dict])
def search_title_endpoint(
    query: str,
    media_type: MediaType | None = None,
    limit: int = 20,
    session: Session = Depends(get_session),
):
    return [
        {
            "id": title.id,
            "title": title.title,
            "media_type": title.media_type,
        }
        for title in search_titles(
            session,
            query=query,
            media_type=media_type,
            limit=limit,
        )
    ]


@title_search_router.get("/external/shikimori/search", response_model=list[dict])
def search_shikimori_endpoint(
    query: str,
    media_type: MediaType | None = None,
    limit: int = 20,
):
    try:
        results = ShikimoriAdapter().search_titles(
            query=query,
            media_type=media_type,
            limit=limit,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Shikimori search failed.",
        ) from exc

    return [
        {
            "external_id": item.external_id,
            "title": item.title,
            "media_type": item.media_type,
            "url": item.url,
            "alternative_titles": item.alternative_titles,
            "description": item.description,
            "cover_url": item.cover_url,
            "release_date": item.release_date,
            "metadata": item.metadata,
        }
        for item in results
    ]


class ShikimoriLinkPayload(BaseModel):
    external_id: str
    title: str
    media_type: MediaType
    url: str | None = None
    alternative_titles: tuple[str, ...] = ()
    description: str | None = None
    cover_url: str | None = None
    release_date: str | None = None
    metadata: dict = {}


class ShikimoriImportPayload(BaseModel):
    user_id: int | None = None
    external_user_id: str
    media_type: MediaType | None = None


@title_search_router.post("/external/shikimori/import", response_model=dict)
def import_shikimori_endpoint(
    payload: ShikimoriImportPayload,
    session: Session = Depends(get_session),
):
    if payload.user_id is None:
        payload.user_id = get_dev_user(session).id
    try:
        report = import_shikimori_rates(
            session,
            user_id=payload.user_id,
            external_user_id=payload.external_user_id,
            adapter=ShikimoriAdapter(),
            media_type=payload.media_type,
        )
        session.commit()
    except Exception as exc:
        session.rollback()
        raise HTTPException(
            status_code=502,
            detail="Shikimori import failed.",
        ) from exc

    return {
        "imported": report.imported,
        "created_titles": report.created_titles,
        "linked_titles": report.linked_titles,
        "conflicts": [
            {
                "external_id": conflict.external_id,
                "title": conflict.title,
                "reason": conflict.reason,
                "candidate_title_ids": conflict.candidate_title_ids,
            }
            for conflict in report.conflicts
        ],
    }


@title_search_router.post("/titles/{title_id}/external/shikimori", response_model=dict)
def link_shikimori_endpoint(
    title_id: int,
    payload: ShikimoriLinkPayload,
    session: Session = Depends(get_session),
):
    try:
        ensure_external_source(
            session,
            key="shikimori",
            name="Shikimori",
            base_url="https://shikimori.one",
        )
        external_title = link_external_title(
            session,
            title_id=title_id,
            source_key="shikimori",
            result=ExternalSearchResult(
                external_id=payload.external_id,
                title=payload.title,
                media_type=payload.media_type,
                url=payload.url,
                alternative_titles=payload.alternative_titles,
                description=payload.description,
                cover_url=payload.cover_url,
                release_date=payload.release_date,
                metadata=payload.metadata,
            ),
        )
        session.commit()
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "id": external_title.id,
        "title_id": external_title.title_id,
        "external_id": external_title.external_id,
        "source": "shikimori",
    }


class LibraryEntryUpdatePayload(BaseModel):
    user_id: int | None
    title_id: int
    list_id: int | None = None
    progress_current: int | None = None
    progress_total: int | None = None
    completed_at: datetime | None = None


@title_search_router.get("/library/entry", response_model=dict)
def get_library_entry_endpoint(
    user_id: int | None,
    title_id: int,
    session: Session = Depends(get_session),
):
    if user_id is None:
        user_id = get_dev_user(session).id
        session.commit()
    entry = get_entry(session, user_id=user_id, title_id=title_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Library entry not found.")
    return {
        "id": entry.id,
        "list_id": entry.list_id,
        "progress_current": entry.progress_current,
        "progress_total": entry.progress_total,
        "completed_at": entry.completed_at,
        "notes": entry.notes,
    }


@title_search_router.put("/library/entry", response_model=dict)
def update_library_entry_endpoint(
    payload: LibraryEntryUpdatePayload,
    session: Session = Depends(get_session),
):
    if payload.user_id is None:
        payload.user_id = get_dev_user(session).id
    try:
        entry = update_entry(
            session,
            user_id=payload.user_id,
            title_id=payload.title_id,
            list_id=payload.list_id,
            progress_current=payload.progress_current,
            progress_total=payload.progress_total,
            completed_at=payload.completed_at,
        )
        session.commit()
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "id": entry.id,
        "list_id": entry.list_id,
        "progress_current": entry.progress_current,
        "progress_total": entry.progress_total,
        "completed_at": entry.completed_at,
    }
