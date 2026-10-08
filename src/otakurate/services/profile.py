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
    rating_rows = session.execute(
        select(UserRating.overall_rating, func.count(UserRating.id))
        .where(UserRating.user_id == user_id)
        .group_by(UserRating.overall_rating)
    )
    rating_counts = {rating: count for rating, count in rating_rows}
    max_rating_count = max(rating_counts.values(), default=0)
    rating_distribution = [
        {
            "rating": rating,
            "count": rating_counts.get(rating, 0),
            "percentage": round(rating_counts.get(rating, 0) / max_rating_count * 100) if max_rating_count else 0,
        }
        for rating in range(1, 11)
    ]
    criteria_totals = {
        MediaType.ANIME: {criterion.value: {"total": 0, "count": 0} for criterion in ANIME_CRITERIA},
        MediaType.MANGA: {criterion.value: {"total": 0, "count": 0} for criterion in MANGA_CRITERIA},
    }
    criteria_rows = session.execute(
        select(UserRating.criteria_values, Title.media_type)
        .join(Title, Title.id == UserRating.title_id)
        .where(UserRating.user_id == user_id)
    )
    for values, media_type in criteria_rows:
        if media_type not in criteria_totals or not isinstance(values, dict):
            continue
        for key, value in values.items():
            if key not in criteria_totals[media_type]:
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not 1 <= value <= 10:
                continue
            criteria_totals[media_type][key]["total"] += value
            criteria_totals[media_type][key]["count"] += 1

    criteria_averages = {}
    for media_type, criteria in ((MediaType.ANIME, ANIME_CRITERIA), (MediaType.MANGA, MANGA_CRITERIA)):
        criteria_averages[media_type.value] = [
            {
                "key": criterion.value,
                "name": CRITERION_INFO[criterion].name,
                "average": (
                    round(criteria_totals[media_type][criterion.value]["total"]
                          / criteria_totals[media_type][criterion.value]["count"], 2)
                    if criteria_totals[media_type][criterion.value]["count"] else None
                ),
                "count": criteria_totals[media_type][criterion.value]["count"],
            }
            for criterion in criteria
        ]

    anime_count = session.scalar(select(func.count(UserRating.id)).join(Title, Title.id == UserRating.title_id).where(UserRating.user_id == user_id, Title.media_type == MediaType.ANIME)) or 0
    manga_count = session.scalar(select(func.count(UserRating.id)).join(Title, Title.id == UserRating.title_id).where(UserRating.user_id == user_id, Title.media_type == MediaType.MANGA)) or 0
    return {
        "rating_count": rating_count,
        "library_count": library_count,
        "average_rating": round(float(average), 2) if average is not None else None,
        "rating_distribution": rating_distribution,
        "criteria_averages": criteria_averages,
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
