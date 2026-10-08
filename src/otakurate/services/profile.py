from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..domain.enums import MediaType
from ..models import LibraryEntry, RatingProfile, RatingProfileCriterion, RatingCriterion, Title, UserRating
from ..rating import ANIME_CRITERIA, CRITERION_INFO, MANGA_CRITERIA
from .rating_profiles import create_rating_profile_version


def get_profile_summary(session: Session, user_id: int) -> dict:
    rating_count = session.scalar(select(func.count(UserRating.id)).where(UserRating.user_id == user_id)) or 0
    library_count = session.scalar(select(func.count(LibraryEntry.id)).where(LibraryEntry.user_id == user_id)) or 0
    average = session.scalar(select(func.avg(UserRating.overall_rating)).where(UserRating.user_id == user_id))
    anime_count = session.scalar(select(func.count(UserRating.id)).join(Title, Title.id == UserRating.title_id).where(UserRating.user_id == user_id, Title.media_type == MediaType.ANIME)) or 0
    manga_count = session.scalar(select(func.count(UserRating.id)).join(Title, Title.id == UserRating.title_id).where(UserRating.user_id == user_id, Title.media_type == MediaType.MANGA)) or 0
    return {
        "rating_count": rating_count,
        "library_count": library_count,
        "average_rating": round(float(average), 2) if average is not None else None,
        "anime_rating_count": anime_count,
        "manga_rating_count": manga_count,
    }


def get_rating_settings(session: Session, user_id: int) -> dict:
    result = {}
    for media_type, criteria in ((MediaType.ANIME, ANIME_CRITERIA), (MediaType.MANGA, MANGA_CRITERIA)):
        profile = session.scalar(
            select(RatingProfile)
            .where(RatingProfile.user_id == user_id, RatingProfile.media_type == media_type)
            .order_by(RatingProfile.version.desc())
        )
        if profile is None:
            profile = session.scalar(
                select(RatingProfile)
                .where(RatingProfile.user_id.is_(None), RatingProfile.media_type == media_type, RatingProfile.is_default.is_(True))
                .order_by(RatingProfile.version.desc())
            )
        weights = {}
        enabled = {}
        if profile is not None:
            rows = session.execute(
                select(RatingCriterion.key, RatingCriterion.name, RatingProfileCriterion.weight, RatingProfileCriterion.enabled)
                .join(RatingProfileCriterion, RatingProfileCriterion.criterion_id == RatingCriterion.id)
                .where(RatingProfileCriterion.profile_id == profile.id)
                .order_by(RatingProfileCriterion.order_index)
            )
            for key, name, weight, is_enabled in rows:
                weights[key] = {"name": name, "weight": weight, "enabled": is_enabled}
        else:
            for criterion in criteria:
                weights[criterion.value] = {"name": CRITERION_INFO[criterion].name, "weight": 1.0, "enabled": True}
        result[media_type.value] = {"version": profile.version if profile else None, "criteria": weights}
    return result


def save_rating_settings(session: Session, *, user_id: int, media_type: MediaType, weights: dict[str, float], enabled: dict[str, bool]) -> RatingProfile:
    return create_rating_profile_version(
        session,
        user_id=user_id,
        media_type=media_type,
        weights=weights,
        enabled=enabled,
        name="Мой профиль",
    )
