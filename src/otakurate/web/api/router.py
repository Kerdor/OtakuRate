from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...database import SessionLocal
from ...domain.enums import MediaType
from ...models import RatingProfile
from ...services.title_search import search_titles
from ...services.user_ratings import save_user_rating

router = APIRouter(prefix="/ratings", tags=["ratings"])
title_search_router = APIRouter(tags=["titles"])


def get_session():
    with SessionLocal() as session:
        yield session


class RatingPayload(BaseModel):
    user_id: int
    title_id: int
    media_type: MediaType
    criteria_values: dict[str, int] = Field(min_length=1)


@router.put("", response_model=dict)
def upsert_rating(payload: RatingPayload, session: Session = Depends(get_session)):
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
