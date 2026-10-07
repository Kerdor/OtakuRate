from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Title, UserRating
from ..rating import calculate_rating, validate_criteria
from .rating_profiles import profile_weights


def save_user_rating(
    session: Session,
    *,
    user_id: int,
    title_id: int,
    criteria_values: dict[str, int],
    profile,
) -> UserRating:
    weights = profile_weights(session, profile)
    validate_criteria(criteria_values)
    if set(criteria_values) != set(weights):
        raise ValueError("Rating criteria must match the profile.")
    overall = calculate_rating(criteria_values, weights)
    rating = session.scalar(
        select(UserRating).where(
            UserRating.user_id == user_id,
            UserRating.title_id == title_id,
        )
    )
    if rating is None:
        rating = UserRating(
            user_id=user_id,
            title_id=title_id,
            overall_rating=overall,
            criteria_values=criteria_values,
            rating_profile_version=profile.version,
        )
        session.add(rating)
    else:
        rating.overall_rating = overall
        rating.criteria_values = criteria_values
        rating.rating_profile_version = profile.version
    session.flush()
    return rating