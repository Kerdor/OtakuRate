from __future__ import annotations

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
