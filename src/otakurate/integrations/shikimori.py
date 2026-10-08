from __future__ import annotations

import json
from datetime import date
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ..domain.enums import MediaType
from .base import ExternalSearchResult


class ShikimoriAdapter:
    key = "shikimori"
    name = "Shikimori"

    def __init__(
        self,
        *,
        base_url: str = "https://shikimori.one",
        timeout: float = 10.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def search_titles(
        self,
        *,
        query: str,
        media_type: MediaType | None = None,
        limit: int = 20,
    ) -> list[ExternalSearchResult]:
        normalized = query.strip()
        if not normalized:
            return []

        types = (
            [media_type]
            if media_type is not None
            else [MediaType.ANIME, MediaType.MANGA]
        )
        results: list[ExternalSearchResult] = []

        for item_type in types:
            endpoint = "animes" if item_type == MediaType.ANIME else "mangas"
            params = urlencode({"search": normalized, "limit": min(limit, 50)})
            request = Request(
                f"{self.base_url}/api/{endpoint}?{params}",
                headers={"User-Agent": "OtakuRate/0.1"},
            )
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.load(response)

            results.extend(
                self._normalize_item(item, media_type=item_type)
                for item in payload
            )

        return results[:limit]

    def _normalize_item(
        self,
        item: dict,
        *,
        media_type: MediaType,
    ) -> ExternalSearchResult:
        external_id = str(item["id"])
        title = item.get("russian") or item.get("name") or external_id
        alternative_titles = tuple(
            value
            for value in (item.get("name"), item.get("russian"))
            if value and value != title
        )
        genres = tuple(
            genre.get("russian") or genre.get("name")
            for genre in item.get("genres", [])
            if genre.get("russian") or genre.get("name")
        )

        release_date = item.get("aired_on") or item.get("released_on")
        if release_date:
            try:
                release_date = date.fromisoformat(release_date).isoformat()
            except ValueError:
                release_date = None

        relative_url = item.get("url")
        url = (
            f"{self.base_url}{relative_url}"
            if relative_url and relative_url.startswith("/")
            else relative_url
        )

        metadata = {
            key: value
            for key, value in {
                "kind": item.get("kind"),
                "status": item.get("status"),
                "score": item.get("score"),
                "episodes": item.get("episodes"),
                "episodes_aired": item.get("episodes_aired"),
                "chapters": item.get("chapters"),
                "volumes": item.get("volumes"),
                "genres": genres,
            }.items()
            if value not in (None, "", ())
        }

        return ExternalSearchResult(
            external_id=external_id,
            title=title,
            media_type=media_type,
            url=url,
            alternative_titles=alternative_titles,
            description=item.get("description"),
            cover_url=item.get("image", {}).get("original"),
            release_date=release_date,
            metadata=metadata,
        )
