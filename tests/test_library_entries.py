from otakurate.domain.enums import MediaType
from otakurate.models import LibraryEntry, Title, User, UserList
from otakurate.services.library_entries import add_to_list
from otakurate.services.titles import create_title


def test_create_title_manual():
    from otakurate.database import SessionLocal

    with SessionLocal() as session:
        title = create_title(session, title="  Test Anime  ", media_type=MediaType.ANIME)
        session.commit()

        assert title.title == "Test Anime"
        assert title.media_type == MediaType.ANIME


def test_add_title_to_matching_user_list():
    from otakurate.database import SessionLocal

    with SessionLocal() as session:
        user = User(username="tester")
        title = Title(title="Test Anime", media_type=MediaType.ANIME)
        user_list = UserList(
            user_id=1,
            media_type=MediaType.ANIME,
            name="Watched",
            system_key="watched",
            is_system=True,
        )
        session.add(user)
        session.flush()
        user_list.user_id = user.id
        session.add_all([title, user_list])
        session.flush()

        entry = add_to_list(
            session,
            user_id=user.id,
            title_id=title.id,
            list_id=user_list.id,
        )
        session.commit()

        assert entry.user_id == user.id
        assert entry.title_id == title.id
        assert entry.list_id == user_list.id


def test_add_title_replaces_existing_list():
    from otakurate.database import SessionLocal

    with SessionLocal() as session:
        user = User(username="tester")
        title = Title(title="Test Anime", media_type=MediaType.ANIME)
        first = UserList(
            user_id=1,
            media_type=MediaType.ANIME,
            name="Plan",
            system_key="plan",
            is_system=True,
        )
        second = UserList(
            user_id=1,
            media_type=MediaType.ANIME,
            name="Watched",
            system_key="watched",
            is_system=True,
        )
        session.add(user)
        session.flush()
        first.user_id = user.id
        second.user_id = user.id
        session.add_all([title, first, second])
        session.flush()

        entry = add_to_list(session, user_id=user.id, title_id=title.id, list_id=first.id)
        entry = add_to_list(session, user_id=user.id, title_id=title.id, list_id=second.id)
        session.commit()

        entries = list(session.query(LibraryEntry).filter_by(user_id=user.id, title_id=title.id))
        assert len(entries) == 1
        assert entries[0].list_id == second.id
