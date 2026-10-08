from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...database import SessionLocal
from ...domain.enums import MediaType
from ...models import Title, User, UserRating
from ...services.profile import get_profile_summary, get_rating_settings, save_rating_settings
from .dependencies import get_current_user

router = APIRouter(tags=["profile"])


def get_session():
    with SessionLocal() as session:
        yield session


class ProfileSettingsPayload(BaseModel):
    display_name: str | None = Field(default=None, max_length=64)
    profile_visibility: str = "private"
    library_visibility: str = "private"
    ratings_visibility: str = "private"


class RatingCriterionSetting(BaseModel):
    weight: float = Field(gt=0, le=100)
    enabled: bool = True


class RatingSettingsPayload(BaseModel):
    media_type: MediaType
    criteria: dict[str, RatingCriterionSetting] = Field(min_length=1)


@router.get("/profile", response_model=dict)
def profile(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    settings = user.settings or {}
    favorite_ids = settings.get("favorite_title_ids", [])
    favorites = []
    if favorite_ids:
        titles = session.scalars(__import__("sqlalchemy").select(Title).where(Title.id.in_(favorite_ids)))
        favorites = [{"id": title.id, "title": title.title, "media_type": title.media_type.value} for title in titles]
    return {
        "id": user.id,
        "username": user.username,
        "display_name": settings.get("display_name") or user.username,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "visibility": settings.get("visibility", {"profile": "private", "library": "private", "ratings": "private"}),
        "favorites": favorites,
        "statistics": get_profile_summary(session, user.id),
        "rating_settings": get_rating_settings(session, user.id),
    }


@router.put("/profile/settings", response_model=dict)
def update_profile_settings(payload: ProfileSettingsPayload, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    allowed = {"private", "friends", "public"}
    if any(value not in allowed for value in (payload.profile_visibility, payload.library_visibility, payload.ratings_visibility)):
        raise HTTPException(status_code=400, detail="Visibility must be private, friends, or public.")
    settings = dict(user.settings or {})
    if payload.display_name is not None:
        settings["display_name"] = payload.display_name.strip() or user.username
    settings["visibility"] = {
        "profile": payload.profile_visibility,
        "library": payload.library_visibility,
        "ratings": payload.ratings_visibility,
    }
    user.settings = settings
    session.commit()
    return {"display_name": settings.get("display_name", user.username), "visibility": settings["visibility"]}


@router.put("/profile/favorites", response_model=dict)
def update_favorites(title_ids: list[int], session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    if len(title_ids) > 10 or len(set(title_ids)) != len(title_ids):
        raise HTTPException(status_code=400, detail="Choose up to 10 unique favorite titles.")
    existing = set(session.scalars(__import__("sqlalchemy").select(Title.id).where(Title.id.in_(title_ids)))) if title_ids else set()
    if existing != set(title_ids):
        raise HTTPException(status_code=400, detail="One or more titles were not found.")
    settings = dict(user.settings or {})
    settings["favorite_title_ids"] = title_ids
    user.settings = settings
    session.commit()
    return {"favorite_title_ids": title_ids}


@router.put("/profile/rating-settings", response_model=dict)
def update_rating_settings(payload: RatingSettingsPayload, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    weights = {key: value.weight for key, value in payload.criteria.items()}
    enabled = {key: value.enabled for key, value in payload.criteria.items()}
    try:
        profile = save_rating_settings(session, user_id=user.id, media_type=payload.media_type, weights=weights, enabled=enabled)
        session.commit()
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"media_type": payload.media_type.value, "version": profile.version}
