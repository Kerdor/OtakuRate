from ..domain.enums import MediaType
from ..integrations.base import (
    ExternalCapability,
    ExternalSearchResult,
    ExternalSourceAdapter,
    TitleSearchAdapter,
)


def search_external_titles(
    adapter: ExternalSourceAdapter,
    *,
    query: str,
    media_type: MediaType | None = None,
    limit: int = 20,
) -> list[ExternalSearchResult]:
    normalized = query.strip()
    if not normalized:
        return []

    limit = max(1, min(limit, 50))
    if not adapter.supports(ExternalCapability.SEARCH_TITLES):
        raise ValueError(f"External source {adapter.key!r} does not support title search.")

    search_adapter: TitleSearchAdapter = adapter
    results = search_adapter.search_titles(
        query=normalized,
        media_type=media_type,
        limit=limit,
    )
    return list(results[:limit])
