from otakurate.database import Base
from otakurate.models import (
    LibraryEntry,
    RatingCriterion,
    RatingProfile,
    RatingProfileCriterion,
    UserList,
    UserRating,
    UserTag,
    LibraryEntryTag,
)


def test_rating_profile_tables_are_registered():
    assert "rating_criteria" in Base.metadata.tables
    assert "rating_profiles" in Base.metadata.tables
    assert "rating_profile_criteria" in Base.metadata.tables


def test_rating_profile_has_version_and_media_type():
    assert RatingProfile.__table__.c.version.nullable is False
    assert RatingProfile.__table__.c.media_type.nullable is False


def test_rating_profile_criterion_has_weight_order_and_enabled():
    columns = RatingProfileCriterion.__table__.c
    assert columns.weight.nullable is False
    assert columns.order_index.nullable is False
    assert columns.enabled.nullable is False


def test_user_rating_stores_profile_version():
    assert UserRating.__table__.c.rating_profile_version.nullable is False


def test_rating_criterion_key_is_unique():
    assert RatingCriterion.__table__.c.key.unique is True


def test_library_models_are_registered():
    assert "library_entries" in Base.metadata.tables
    assert "user_lists" in Base.metadata.tables
    assert "user_tags" in Base.metadata.tables
    assert "library_entry_tags" in Base.metadata.tables


def test_library_entry_has_user_title_unique_constraint_and_list():
    columns = LibraryEntry.__table__.c
    assert columns.list_id.nullable is False
    assert columns.progress_current.nullable is True
    assert columns.progress_total.nullable is True
    constraints = LibraryEntry.__table__.constraints
    assert any(
        constraint.name == "uq_library_entries_user_title"
        for constraint in constraints
    )
    assert any(
        constraint.name == "ck_library_entries_progress_current_nonnegative"
        for constraint in constraints
    )
    assert any(
        constraint.name == "ck_library_entries_progress_total_positive"
        for constraint in constraints
    )
    assert any(
        constraint.name == "ck_library_entries_progress_not_over_total"
        for constraint in constraints
    )


def test_user_list_has_media_type_and_system_metadata():
    columns = UserList.__table__.c
    assert columns.media_type.nullable is False
    assert columns.name.nullable is False
    assert columns.is_system.nullable is False


def test_user_tag_belongs_to_user_and_entry_tag_is_composite_key():
    assert UserTag.__table__.c.user_id.nullable is False
    assert LibraryEntryTag.__table__.c.library_entry_id.primary_key is True
    assert LibraryEntryTag.__table__.c.tag_id.primary_key is True


def test_anime_progress_represents_watched_episodes():
    from otakurate.domain.enums import MediaType
    from otakurate.models import Title

    anime = Title(title="Test Anime", media_type=MediaType.ANIME)

    assert anime.media_type is MediaType.ANIME
    entry_columns = LibraryEntry.__table__.c
    assert entry_columns.progress_current.nullable is True
    assert entry_columns.progress_total.nullable is True
