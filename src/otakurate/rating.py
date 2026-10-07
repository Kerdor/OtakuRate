from dataclasses import dataclass


@dataclass(frozen=True)
class Rating:
    value: float


def validate_rating(value: float) -> float:
    if not 1 <= value <= 10:
        raise ValueError("Rating must be between 1 and 10.")
    return round(value, 2)
