from otakurate.integrations.base import ExternalCapability
from otakurate.integrations.shikimori import ShikimoriAdapter


def test_shikimori_declares_only_supported_capabilities():
    adapter = ShikimoriAdapter()

    assert adapter.supports(ExternalCapability.SEARCH_TITLES)
    assert adapter.supports(ExternalCapability.GET_USER_LIST)
    assert not adapter.supports(ExternalCapability.GET_TITLE)
    assert not adapter.supports(ExternalCapability.GET_RATING)
    assert not adapter.supports(ExternalCapability.SET_RATING)
    assert not adapter.supports(ExternalCapability.GET_STATUS)
    assert not adapter.supports(ExternalCapability.SET_STATUS)
    assert not adapter.supports(ExternalCapability.GET_PROGRESS)
    assert not adapter.supports(ExternalCapability.SET_PROGRESS)


def test_capability_names_are_stable():
    assert ExternalCapability.SEARCH_TITLES.value == "search_titles"
    assert ExternalCapability.GET_USER_LIST.value == "get_user_list"
    assert ExternalCapability.GET_RATING.value == "get_rating"
    assert ExternalCapability.SET_RATING.value == "set_rating"
    assert ExternalCapability.GET_STATUS.value == "get_status"
    assert ExternalCapability.SET_STATUS.value == "set_status"
    assert ExternalCapability.GET_PROGRESS.value == "get_progress"
    assert ExternalCapability.SET_PROGRESS.value == "set_progress"
