from collections.abc import Iterable


def resolve_progress_total(values: Iterable[int | None]) -> int | None:
    """Return the maximum confirmed positive total from available sources."""
    confirmed = [value for value in values if value is not None and value > 0]
    return max(confirmed) if confirmed else None
