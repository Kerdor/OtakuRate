from .base import (
    ExternalCapability,
    ExternalSearchResult,
    ExternalSourceAdapter,
    TitleSearchAdapter,
    UserListAdapter,
)
from .shikimori import ShikimoriAdapter
from .registry import IntegrationRegistry, create_default_registry, default_registry

__all__ = [
    "ExternalCapability",
    "ExternalSearchResult",
    "ExternalSourceAdapter",
    "TitleSearchAdapter",
    "UserListAdapter",
    "ShikimoriAdapter",
    "IntegrationRegistry",
    "create_default_registry",
    "default_registry",
]
