from otakurate.domain.enums import MediaType
from otakurate.domain.types import TitleId, UserId


def test_media_type_values():
    assert MediaType.ANIME.value == "anime"
    assert MediaType.MANGA.value == "manga"


def test_domain_identifier_types_are_int_compatible():
    assert UserId(1) == 1
    assert TitleId(1) == 1
