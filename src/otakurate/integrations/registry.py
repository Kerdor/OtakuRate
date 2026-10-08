from collections.abc import Callable
from typing import TypeVar

from .base import ExternalSourceAdapter
from .shikimori import ShikimoriAdapter


AdapterT = TypeVar("AdapterT", bound=ExternalSourceAdapter)


class IntegrationRegistry:
    """Registry for external adapters.

    Core services depend on this registry rather than concrete source classes.
    New integrations can be registered without changing domain or service code.
    """

    def __init__(self) -> None:
        self._factories: dict[str, Callable[[], ExternalSourceAdapter]] = {}

    def register(
        self,
        adapter_or_factory: type[AdapterT] | Callable[[], AdapterT],
    ) -> None:
        adapter = adapter_or_factory()
        if adapter.key in self._factories:
            raise ValueError(f"External source {adapter.key!r} is already registered.")
        self._factories[adapter.key] = adapter_or_factory

    def create(self, key: str) -> ExternalSourceAdapter:
        try:
            factory = self._factories[key]
        except KeyError as exc:
            raise KeyError(f"Unknown external source: {key!r}") from exc
        return factory()

    def keys(self) -> tuple[str, ...]:
        return tuple(self._factories)


def create_default_registry() -> IntegrationRegistry:
    registry = IntegrationRegistry()
    registry.register(ShikimoriAdapter)
    return registry


default_registry = create_default_registry()


__all__ = [
    "IntegrationRegistry",
    "create_default_registry",
    "default_registry",
]
