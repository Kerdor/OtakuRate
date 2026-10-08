from dataclasses import dataclass, field
from typing import Protocol

from ..domain.enums import MediaType


@dataclass(frozen=True)
class ExternalSearchResult:
    external_id: str
    title: str
    media_type: MediaType
    url: str | None = None
    alternative_titles: tuple[str, ...] = ()
    description: str | None = None
    cover_url: str | None = None
    release_date: str | None = None
    metadata: dict = field(default_factory=dict)


class ExternalSourceAdapter(Protocol):
    key: str
    name: str

    def search_titles(
        self,
        *,
        query: str,
        media_type: MediaType | None = None,
        limit: int = 20,
    ) -> list[ExternalSearchResult]:
        ...
