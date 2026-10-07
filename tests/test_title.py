from datetime import date

from otakurate.database import Base
from otakurate.domain.enums import MediaType
from otakurate.models import ReleaseStatus, Title


def test_title_model_is_registered():
    assert "titles" in Base.metadata.tables


def test_title_supports_anime_metadata():
    title = Title(
        title="Test Anime",
        media_type=MediaType.ANIME,
        alternative_titles=["Alternative"],
        description="Description",
        cover_url="https://example.com/cover.jpg",
        release_date=date(2026, 1, 2),
        release_status=ReleaseStatus.FINISHED,
        genres=["Action"],
        tags=["Original"],
        metadata={"episodes": 12},
    )

    assert title.title == "Test Anime"
    assert title.alternative_titles == ["Alternative"]
    assert title.media_type == MediaType.ANIME
    assert title.description == "Description"
    assert title.cover_url.endswith("cover.jpg")
    assert title.release_date == date(2026, 1, 2)
    assert title.release_status == ReleaseStatus.FINISHED
    assert title.genres == ["Action"]
    assert title.tags == ["Original"]
    assert title.metadata == {"episodes": 12}
