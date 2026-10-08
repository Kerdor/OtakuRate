import pytest

from otakurate.domain.enums import MediaType
from otakurate.integrations.mapping import map_media_type, map_progress, map_rating, map_status, normalize_external_id, normalize_title_name, classify_title_identity


def test_status_mapping():
    assert map_status(MediaType.ANIME, "rewatching") == "watching"
    assert map_status(MediaType.MANGA, "watching") == "reading"
    assert map_status(MediaType.ANIME, "unknown") is None


def test_media_type_mapping():
    assert map_media_type("ANIMES") == MediaType.ANIME
    assert map_media_type("manhwa") == MediaType.MANGA
    with pytest.raises(ValueError):
        map_media_type("book")


def test_external_id_normalization():
    assert normalize_external_id(" 001 ") == "001"
    assert normalize_external_id(42) == "42"
    with pytest.raises(ValueError):
        normalize_external_id(" ")


def test_progress_mapping():
    result = map_progress("4", "12")
    assert (result.current, result.total) == (4, 12)
    assert map_progress(None, 12).current is None
    assert map_progress(-1, 12).current is None
    assert map_progress(15, 12).total == 15


def test_rating_mapping():
    assert map_rating(8) == pytest.approx(8)
    assert map_rating(0) is None
    assert map_rating(5, source_min=0.5, source_max=5) == pytest.approx(10)
    assert map_rating(11) is None


def test_name_normalization_and_identity_rules():
    assert normalize_title_name(" ＴＥＳＴ   Anime ") == "test anime"
    match = classify_title_identity(source_key="shikimori", external_id=12, media_type=MediaType.ANIME, external_title="TEST", existing_source_key="mangalib", existing_external_id="12", existing_media_type=MediaType.ANIME, existing_title=" test ")
    assert match.kind == "candidate"
    exact = classify_title_identity(source_key="shikimori", external_id=12, media_type=MediaType.ANIME, external_title="New name", existing_source_key="shikimori", existing_external_id="12", existing_media_type=MediaType.ANIME, existing_title="Old name")
    assert exact.kind == "exact"
    different = classify_title_identity(source_key="shikimori", external_id=12, media_type=MediaType.ANIME, external_title="TEST", existing_media_type=MediaType.MANGA, existing_title="TEST")
    assert different.kind == "different"
