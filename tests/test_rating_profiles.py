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


def test_manga_progress_represents_read_chapters():
    from otakurate.domain.enums import MediaType
    from otakurate.models import Title

    manga = Title(title="Test Manga", media_type=MediaType.MANGA)

    assert manga.media_type is MediaType.MANGA
    entry_columns = LibraryEntry.__table__.c
    assert entry_columns.progress_current.nullable is True
    assert entry_columns.progress_total.nullable is True


def test_progress_total_uses_maximum_confirmed_source_value():
    from otakurate.domain.progress import resolve_progress_total

    assert resolve_progress_total([12, 10, None, 8]) == 12
    assert resolve_progress_total([None, 0, -1]) is None



def test_library_entry_has_added_at_timestamp():
    columns = LibraryEntry.__table__.c

    assert columns.created_at.nullable is False
    assert columns.created_at.type.__class__.__name__ == "DateTime"



def test_library_entry_has_optional_completion_timestamp():
    columns = LibraryEntry.__table__.c

    assert columns.completed_at.nullable is True
    assert columns.completed_at.type.__class__.__name__ == "DateTime"



def test_library_entry_has_optional_notes():
    columns = LibraryEntry.__table__.c

    assert columns.notes.nullable is True
    assert columns.notes.type.__class__.__name__ == "Text"


def test_library_filters_are_optional_and_combinable():
    from datetime import datetime, timezone

    from otakurate.database import SessionLocal
    from otakurate.domain.enums import MediaType
    from otakurate.models import Title, User

    from otakurate.services.library import LibraryFilters, filter_library

    with SessionLocal() as session:
        user = User(username="filter-user")
        other_user = User(username="other-user")
        session.add_all([user, other_user])
        session.flush()

        anime = Title(title="Anime", media_type=MediaType.ANIME)
        manga = Title(title="Manga", media_type=MediaType.MANGA)
        other_title = Title(title="Other", media_type=MediaType.ANIME)
        session.add_all([anime, manga, other_title])
        session.flush()

        from otakurate.models import UserList, UserRating, UserTag, LibraryEntry, LibraryEntryTag

        watched = UserList(
            user_id=user.id,
            media_type=MediaType.ANIME,
            name="Watched",
            system_key="watched",
            is_system=True,
        )
        reading = UserList(
            user_id=user.id,
            media_type=MediaType.MANGA,
            name="Reading",
            system_key="reading",
            is_system=True,
        )
        other_list = UserList(
            user_id=other_user.id,
            media_type=MediaType.ANIME,
            name="Watched",
            system_key="watched",
            is_system=True,
        )
        session.add_all([watched, reading, other_list])
        session.flush()

        anime_entry = LibraryEntry(
            user_id=user.id,
            title_id=anime.id,
            list_id=watched.id,
            progress_current=5,
            progress_total=12,
            completed_at=datetime(2026, 1, 10, tzinfo=timezone.utc),
            notes="keep",
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        manga_entry = LibraryEntry(
            user_id=user.id,
            title_id=manga.id,
            list_id=reading.id,
            created_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
        )
        other_entry = LibraryEntry(
            user_id=other_user.id,
            title_id=other_title.id,
            list_id=other_list.id,
        )
        session.add_all([anime_entry, manga_entry, other_entry])
        session.flush()

        tag = UserTag(user_id=user.id, name="favorite")
        second_tag = UserTag(user_id=user.id, name="rewatch")
        other_tag = UserTag(user_id=other_user.id, name="favorite")
        session.add_all([tag, second_tag, other_tag])
        session.flush()

        session.add_all(
            [
                LibraryEntryTag(
                    library_entry_id=anime_entry.id,
                    tag_id=tag.id,
                ),
                LibraryEntryTag(
                    library_entry_id=anime_entry.id,
                    tag_id=second_tag.id,
                ),
            ]
        )
        session.add_all(
            [
                UserRating(
                    user_id=user.id,
                    title_id=anime.id,
                    overall_rating=9,
                    criteria_values={},
                    rating_profile_version=1,
                ),
                UserRating(
                    user_id=user.id,
                    title_id=manga.id,
                    overall_rating=6,
                    criteria_values={},
                    rating_profile_version=1,
                ),
            ]
        )
        session.commit()

        assert [entry.id for entry in filter_library(session, user_id=user.id)] == [
            manga_entry.id,
            anime_entry.id,
        ]
        assert filter_library(
            session,
            user_id=user.id,
            filters=LibraryFilters(media_type=MediaType.ANIME),
        ) == [anime_entry]
        assert filter_library(
            session,
            user_id=user.id,
            filters=LibraryFilters(min_rating=8, max_rating=10),
        ) == [anime_entry]
        assert filter_library(
            session,
            user_id=user.id,
            filters=LibraryFilters(has_progress=True, completed=True, has_notes=True),
        ) == [anime_entry]
        assert filter_library(
            session,
            user_id=user.id,
            filters=LibraryFilters(has_progress=False, completed=False, has_notes=False),
        ) == [manga_entry]
        assert filter_library(
            session,
            user_id=user.id,
            filters=LibraryFilters(tag_ids=(tag.id, second_tag.id)),
        ) == [anime_entry]
        assert filter_library(
            session,
            user_id=user.id,
            filters=LibraryFilters(
                added_from=datetime(2026, 1, 1, tzinfo=timezone.utc),
                added_to=datetime(2026, 1, 31, 23, 59, tzinfo=timezone.utc),
                completed_from=datetime(2026, 1, 1, tzinfo=timezone.utc),
                completed_to=datetime(2026, 1, 31, 23, 59, tzinfo=timezone.utc),
            ),
        ) == [anime_entry]


def test_library_sorting():
    from datetime import datetime, timezone

    from otakurate.database import SessionLocal
    from otakurate.domain.enums import MediaType
    from otakurate.models import Title, User
    from otakurate.services.library import LibrarySort, filter_library

    with SessionLocal() as session:
        user = User(username="sort-user")
        session.add(user)
        session.flush()

        titles = [
            Title(title="Zeta", media_type=MediaType.ANIME),
            Title(title="Alpha", media_type=MediaType.ANIME),
            Title(title="Beta", media_type=MediaType.ANIME),
        ]
        session.add_all(titles)
        session.flush()

        user_list = UserList(
            user_id=user.id, media_type=MediaType.ANIME,
            name="Watching", system_key="watching", is_system=True,
        )
        session.add(user_list)
        session.flush()

        entries = [
            LibraryEntry(
                user_id=user.id, title_id=titles[0].id, list_id=user_list.id,
                progress_current=5,
                completed_at=datetime(2026, 1, 3, tzinfo=timezone.utc),
                created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                updated_at=datetime(2026, 1, 5, tzinfo=timezone.utc),
            ),
            LibraryEntry(
                user_id=user.id, title_id=titles[1].id, list_id=user_list.id,
                progress_current=10,
                completed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
                updated_at=datetime(2026, 1, 4, tzinfo=timezone.utc),
            ),
            LibraryEntry(
                user_id=user.id, title_id=titles[2].id, list_id=user_list.id,
                progress_current=None, completed_at=None,
                created_at=datetime(2026, 1, 3, tzinfo=timezone.utc),
                updated_at=datetime(2026, 1, 6, tzinfo=timezone.utc),
            ),
        ]
        session.add_all(entries)
        session.add_all([
            UserRating(user_id=user.id, title_id=titles[0].id, overall_rating=7,
                       criteria_values={}, rating_profile_version=1),
            UserRating(user_id=user.id, title_id=titles[1].id, overall_rating=9,
                       criteria_values={}, rating_profile_version=1),
        ])
        session.commit()

        assert [e.created_at for e in filter_library(session, user_id=user.id)] == [
            entries[2].created_at,
            entries[1].created_at,
            entries[0].created_at,
        ]
        assert [e.created_at for e in filter_library(session, user_id=user.id, sort=LibrarySort.ADDED_OLDEST)] == [
            entries[0].created_at,
            entries[1].created_at,
            entries[2].created_at,
        ]
        assert [e.title_id for e in filter_library(session, user_id=user.id, sort=LibrarySort.TITLE_ASC)] == [titles[1].id, titles[2].id, titles[0].id]
        assert [e.title_id for e in filter_library(session, user_id=user.id, sort=LibrarySort.TITLE_DESC)] == [titles[0].id, titles[2].id, titles[1].id]
        assert [e.title_id for e in filter_library(session, user_id=user.id, sort=LibrarySort.RATING_HIGH)] == [titles[1].id, titles[0].id, titles[2].id]
        assert [e.title_id for e in filter_library(session, user_id=user.id, sort=LibrarySort.RATING_LOW)] == [titles[0].id, titles[1].id, titles[2].id]
        assert [e.title_id for e in filter_library(session, user_id=user.id, sort=LibrarySort.PROGRESS_HIGH)] == [titles[1].id, titles[0].id, titles[2].id]
        assert [e.title_id for e in filter_library(session, user_id=user.id, sort=LibrarySort.PROGRESS_LOW)] == [titles[0].id, titles[1].id, titles[2].id]
        assert [e.title_id for e in filter_library(session, user_id=user.id, sort=LibrarySort.COMPLETED_NEWEST)] == [titles[0].id, titles[1].id, titles[2].id]
        assert [e.title_id for e in filter_library(session, user_id=user.id, sort=LibrarySort.COMPLETED_OLDEST)] == [titles[1].id, titles[0].id, titles[2].id]
        assert [e.title_id for e in filter_library(session, user_id=user.id, sort=LibrarySort.UPDATED_NEWEST)] == [titles[2].id, titles[0].id, titles[1].id]
