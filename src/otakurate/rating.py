from dataclasses import dataclass
from enum import StrEnum


class RatingCriterion(StrEnum):
    STORY = "story"
    CHARACTERS = "characters"
    EMOTIONS = "emotions"
    INTEREST = "interest"
    ATMOSPHERE = "atmosphere"
    WORLD = "world"
    DEVELOPMENT = "development"
    VISUALS = "visuals"
    SOUND = "sound"
    AFTERTASTE = "aftertaste"


ANIME_CRITERIA: tuple[RatingCriterion, ...] = (
    RatingCriterion.STORY,
    RatingCriterion.CHARACTERS,
    RatingCriterion.EMOTIONS,
    RatingCriterion.INTEREST,
    RatingCriterion.ATMOSPHERE,
    RatingCriterion.WORLD,
    RatingCriterion.DEVELOPMENT,
    RatingCriterion.VISUALS,
    RatingCriterion.SOUND,
    RatingCriterion.AFTERTASTE,
)


@dataclass(frozen=True)
class Rating:
    value: int


def validate_rating(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("Rating must be an integer.")
    if not 1 <= value <= 10:
        raise ValueError("Rating must be between 1 and 10.")
    return value


def validate_criteria(criteria: dict[str, int]) -> dict[str, int]:
    if not isinstance(criteria, dict):
        raise ValueError("Criteria must be a dictionary.")
    return {name: validate_rating(value) for name, value in criteria.items()}


def calculate_rating(criteria: dict[str, int], weights: dict[str, float] | None = None) -> int:
    validated = validate_criteria(criteria)
    if not validated:
        raise ValueError("At least one criterion is required.")
    if weights is None:
        weights = {name: 1.0 for name in validated}
    if set(weights) != set(validated):
        raise ValueError("Weights must match criteria exactly.")
    if any(weight <= 0 for weight in weights.values()):
        raise ValueError("Weights must be positive.")
    total_weight = sum(weights.values())
    weighted_average = sum(validated[name] * weights[name] for name in validated) / total_weight
    return round(weighted_average)
