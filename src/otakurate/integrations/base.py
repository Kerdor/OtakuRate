from dataclasses import dataclass, field
from enum import StrEnum
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


class ExternalCapability(StrEnum):
    SEARCH_TITLES = "search_titles"
    GET_TITLE = "get_title"
    GET_USER_LIST = "get_user_list"
    GET_RATING = "get_rating"
    SET_RATING = "set_rating"
    GET_STATUS = "get_status"
    SET_STATUS = "set_status"
    GET_PROGRESS = "get_progress"
    SET_PROGRESS = "set_progress"


class ExternalSourceAdapter(Protocol):
    """
    Common identity/capability contract for every external integration.

    Operation-specific protocols below are intentionally separate: an adapter
    only implements the operations it actually supports.
    """

    key: str
    name: str
    capabilities: frozenset[ExternalCapability]

    def supports(self, capability: ExternalCapability) -> bool:
        ...


class TitleSearchAdapter(Protocol):
    def search_titles(
        self,
        *,
        query: str,
        media_type: MediaType | None = None,
        limit: int = 20,
    ) -> list[ExternalSearchResult]:
        ...


class UserListAdapter(Protocol):
    def get_user_list(
        self,
        *,
        external_user_id: str,
        media_type: MediaType | None = None,
        limit: int = 5000,
    ) -> list[dict]:
        ...
