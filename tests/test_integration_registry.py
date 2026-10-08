from otakurate.integrations import ExternalCapability
from otakurate.integrations.registry import IntegrationRegistry


class FakeAdapter:
    key = "fake"
    name = "Fake"
    capabilities = frozenset({ExternalCapability.SEARCH_TITLES})

    def supports(self, capability):
        return capability in self.capabilities


def test_registry_contains_shikimori_without_hardcoding_it_in_services():
    registry = IntegrationRegistry()
    registry.register(FakeAdapter)

    adapter = registry.create("fake")

    assert adapter.key == "fake"
    assert registry.keys() == ("fake",)


def test_registry_rejects_duplicate_keys():
    registry = IntegrationRegistry()
    registry.register(FakeAdapter)

    try:
        registry.register(FakeAdapter)
    except ValueError as exc:
        assert "already registered" in str(exc)
    else:
        raise AssertionError("Duplicate adapter registration should fail.")


def test_default_registry_registers_shikimori():
    from otakurate.integrations import default_registry

    assert "shikimori" in default_registry.keys()
    assert default_registry.create("shikimori").key == "shikimori"


def test_registry_rejects_unknown_source():
    registry = IntegrationRegistry()

    try:
        registry.create("unknown")
    except KeyError as exc:
        assert "unknown" in str(exc)
    else:
        raise AssertionError("Unknown source should fail.")
