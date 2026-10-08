from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from ..domain.enums import MediaType


def map_media_type(value: MediaType | str) -> MediaType:
    if isinstance(value, MediaType):
        return value
    aliases = {
        "anime": MediaType.ANIME,
        "animes": MediaType.ANIME,
        "series": MediaType.ANIME,
        "manga": MediaType.MANGA,
        "mangas": MediaType.MANGA,
        "manhwa": MediaType.MANGA,
        "comics": MediaType.MANGA,
    }
    normalized = str(value).strip().casefold()
    try:
        return aliases[normalized]
    except KeyError as exc:
        raise ValueError(f"Unsupported media type: {value!r}") from exc


STATUS_MAP: dict[MediaType, dict[str, str]] = {
    MediaType.ANIME: {
        "watching": "watching",
        "rewatching": "watching",
        "completed": "completed",
        "planned": "planned",
        "on_hold": "paused",
        "paused": "paused",
        "dropped": "dropped",
    },
    MediaType.MANGA: {
        "watching": "reading",
        "reading": "reading",
        "rewatching": "reading",
        "completed": "completed",
        "planned": "planned",
        "on_hold": "paused",
        "paused": "paused",
        "dropped": "dropped",
    },
}


def map_status(media_type: MediaType, external_status: str | None) -> str | None:
    if not external_status:
        return None
    return STATUS_MAP.get(media_type, {}).get(external_status.strip().casefold())


def normalize_external_id(value: object) -> str:
    if value is None:
        raise ValueError("External ID cannot be empty.")
    normalized = str(value).strip()
    if not normalized:
        raise ValueError("External ID cannot be empty.")
    return normalized


@dataclass(frozen=True)
class NormalizedProgress:
    current: int | None
    total: int | None


def map_progress(current: int | str | None, total: int | str | None) -> NormalizedProgress:
    current_value = _nonnegative_int(current)
    total_value = _positive_int(total)
    if current_value is not None and total_value is not None and current_value > total_value:
        total_value = current_value
    return NormalizedProgress(current=current_value, total=total_value)


def map_rating(
    value: int | float | str | None,
    *,
    source_min: float = 1,
    source_max: float = 10,
) -> float | None:
    """Convert a rated value to OtakuRate's 1–10 scale; 0 means unrated."""
    if value in (None, ""):
        return None
    try:
        rating = float(value)
    except (TypeError, ValueError):
        return None
    if rating == 0 or source_max <= source_min or not source_min <= rating <= source_max:
        return None
    return 1 + ((rating - source_min) / (source_max - source_min)) * 9


def normalize_title_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"\\s+", " ", normalized).strip()


@dataclass(frozen=True)
class TitleIdentityMatch:
    kind: str
    title_id: int | None
    reason: str


def classify_title_identity(
    *,
    source_key: str,
    external_id: object,
    media_type: MediaType,
    external_title: str,
    existing_source_key: str | None = None,
    existing_external_id: object | None = None,
    existing_media_type: MediaType | None = None,
    existing_title: str | None = None,
) -> TitleIdentityMatch:
    """Names only create manual-review candidates; they never trigger auto-merge."""
    ext_id = normalize_external_id(external_id)
    if existing_source_key is not None and existing_external_id is not None:
        same_source = source_key.strip().casefold() == existing_source_key.strip().casefold()
        same_id = ext_id == normalize_external_id(existing_external_id)
        if same_source and same_id:
            if existing_media_type is not None and existing_media_type != media_type:
                return TitleIdentityMatch("conflict", None, "External ID media type mismatch.")
            return TitleIdentityMatch("exact", None, "Same source and external ID.")
    if existing_media_type is not None and existing_media_type != media_type:
        return TitleIdentityMatch("different", None, "Media types differ.")
    if existing_title and normalize_title_name(external_title) == normalize_title_name(existing_title):
        return TitleIdentityMatch("candidate", None, "Same normalized name; manual confirmation required.")
    return TitleIdentityMatch("different", None, "No reliable identity match.")


def _nonnegative_int(value: int | str | None) -> int | None:
    if value in (None, ""):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _positive_int(value: int | str | None) -> int | None:
    parsed = _nonnegative_int(value)
    return parsed if parsed is not None and parsed > 0 else None
