from .base import (
    ExternalCapability,
    ExternalSearchResult,
    ExternalSourceAdapter,
    TitleSearchAdapter,
    UserListAdapter,
)
from .shikimori import ShikimoriAdapter\nfrom .registry import IntegrationRegistry, create_default_registry, default_registry

__all__ = [
    "ExternalCapability",
    "ExternalSearchResult",
    "ExternalSourceAdapter",
    "TitleSearchAdapter",
    "UserListAdapter",
    "ShikimoriAdapter",\n    "IntegrationRegistry",\n    "create_default_registry",\n    "default_registry",
]
