from otakurate.domain.enums import MediaType
from otakurate.integrations.base import ExternalCapability, ExternalSearchResult
from otakurate.services.external_search import search_external_titles


class FakeAdapter:
    key = "fake"
    name = "Fake"

    capabilities = frozenset({ExternalCapability.SEARCH_TITLES})

    def supports(self, capability):
        return capability in self.capabilities

    def __init__(self):
        self.calls = []

    def search_titles(self, *, query, media_type=None, limit=20):
        self.calls.append((query, media_type, limit))
        return [
            ExternalSearchResult(
                external_id="1",
                title="Test",
                media_type=media_type or MediaType.ANIME,
            ),
            ExternalSearchResult(
                external_id="2",
                title="Test 2",
                media_type=media_type or MediaType.ANIME,
            ),
        ]


def test_external_search_normalizes_query_and_limit():
    adapter = FakeAdapter()
    result = search_external_titles(
        adapter,
        query="  test  ",
        media_type=MediaType.ANIME,
        limit=100,
    )

    assert adapter.calls == [("test", MediaType.ANIME, 50)]
    assert [item.external_id for item in result] == ["1", "2"]


def test_external_search_empty_query_does_not_call_adapter():
    adapter = FakeAdapter()

    assert search_external_titles(adapter, query="   ") == []
    assert adapter.calls == []
