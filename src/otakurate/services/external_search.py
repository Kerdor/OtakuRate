from ..domain.enums import MediaType
from ..integrations.base import ExternalSearchResult, ExternalSourceAdapter


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
    results = adapter.search_titles(
        query=normalized,
        media_type=media_type,
        limit=limit,
    )
    return list(results[:limit])
