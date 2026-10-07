"""Application helpers for immutable rating profile versions."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..domain.enums import MediaType
from ..models import RatingCriterion, RatingProfile, RatingProfileCriterion
from ..rating import ANIME_CRITERIA, MANGA_CRITERIA


def create_rating_profile_version(
    session: Session,
    *,
    user_id: int,
    media_type: MediaType,
    weights: dict[str, float],
    enabled: dict[str, bool] | None = None,
    name: str = "Мой профиль",
) -> RatingProfile:
    keys = ANIME_CRITERIA if media_type == MediaType.ANIME else MANGA_CRITERIA
    expected = {criterion.value for criterion in keys}
    if set(weights) != expected:
        raise ValueError("Weights must contain exactly the criteria for this media type.")
    if any(weight <= 0 for weight in weights.values()):
        raise ValueError("Weights must be positive.")
    if enabled is not None and set(enabled) != expected:
        raise ValueError("Enabled flags must contain exactly the criteria for this media type.")
    if enabled is not None and not any(enabled.values()):
        raise ValueError("At least one criterion must be enabled.")

    latest = session.scalar(
        select(RatingProfile)
        .where(
            RatingProfile.user_id == user_id,
            RatingProfile.media_type == media_type,
        )
        .order_by(RatingProfile.version.desc())
    )
    version = 1 if latest is None else latest.version + 1

    profile = RatingProfile(
        user_id=user_id,
        media_type=media_type,
        profile_key="custom",
        name=name,
        version=version,
        is_default=False,
    )
    session.add(profile)
    session.flush()

    criterion_rows = {
        row.key: row
        for row in session.scalars(select(RatingCriterion).where(RatingCriterion.key.in_(expected)))
    }
    if len(criterion_rows) != len(expected):
        raise ValueError("Rating criteria are not initialized in the database.")

    for order_index, key in enumerate(keys):
        session.add(
            RatingProfileCriterion(
                profile_id=profile.id,
                criterion_id=criterion_rows[key.value].id,
                weight=weights[key.value],
                order_index=order_index,
                enabled=True if enabled is None else enabled[key.value],
            )
        )

    return profile


def profile_weights(session: Session, profile: RatingProfile) -> dict[str, float]:
    rows = session.execute(
        select(RatingCriterion.key, RatingProfileCriterion.weight)
        .join(RatingProfileCriterion, RatingProfileCriterion.criterion_id == RatingCriterion.id)
        .where(
            RatingProfileCriterion.profile_id == profile.id,
            RatingProfileCriterion.enabled.is_(True),
        )
        .order_by(RatingProfileCriterion.order_index)
    )
    return {key: weight for key, weight in rows}

def recalculate_user_rating(session: Session, rating_id: int):
    from ..models import Title, UserRating
    from ..rating import calculate_rating

    user_rating = session.get(UserRating, rating_id)
    if user_rating is None:
        raise ValueError("User rating was not found.")

    title = session.get(Title, user_rating.title_id)
    if title is None:
        raise ValueError("Title was not found.")

    profile = session.scalar(
        select(RatingProfile)
        .where(
            RatingProfile.user_id == user_rating.user_id,
            RatingProfile.media_type == title.media_type,
        )
        .order_by(RatingProfile.version.desc())
    )
    if profile is None:
        profile = session.scalar(
            select(RatingProfile)
            .where(
                RatingProfile.user_id.is_(None),
                RatingProfile.media_type == title.media_type,
                RatingProfile.is_default.is_(True),
            )
            .order_by(RatingProfile.version.desc())
        )
    if profile is None:
        raise ValueError("No rating profile is available for this media type.")

    weights = profile_weights(session, profile)
    criteria = {key: user_rating.criteria_values[key] for key in weights if key in user_rating.criteria_values}
    if set(criteria) != set(weights):
        raise ValueError("The rating does not contain all criteria required by the current profile.")

    user_rating.overall_rating = calculate_rating(criteria, weights)
    user_rating.rating_profile_version = profile.version
    return user_rating