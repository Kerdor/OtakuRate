from sqlalchemy import select

from otakurate.database import SessionLocal
from otakurate.domain.enums import MediaType
from otakurate.models import (
    ExternalTitle,
    LibraryEntry,
    Title,
    User,
    UserExternalRating,
    UserList,
)
from otakurate.services.external_import import import_shikimori_rates


def test_import_shikimori_creates_title_entry_and_external_rating():
    with SessionLocal.begin() as session:
        user = User(username="import-user")
        session.add(user)
        session.flush()
        session.add_all(
            [
                UserList(user_id=user.id, media_type=MediaType.ANIME, name="Watching", system_key="watching", is_system=True),
                UserList(user_id=user.id, media_type=MediaType.ANIME, name="Completed", system_key="completed", is_system=True),
                UserList(user_id=user.id, media_type=MediaType.ANIME, name="Plan", system_key="planned", is_system=True),
                UserList(user_id=user.id, media_type=MediaType.ANIME, name="Paused", system_key="paused", is_system=True),
                UserList(user_id=user.id, media_type=MediaType.ANIME, name="Dropped", system_key="dropped", is_system=True),
            ]
        )

        class Adapter:
            def fetch_user_rates(self, **kwargs):
                return [
                    {
                        "target_id": 42,
                        "target_type": "Anime",
                        "status": "completed",
                        "score": 8,
                        "anime": {
                            "id": 42,
                            "name": "Test Anime",
                            "russian": "Тестовое аниме",
                        },
                    }
                ]

            def _normalize_user_rate(self, item):
                return {
                    "external_id": "42",
                    "media_type": MediaType.ANIME,
                    "status": "completed",
                    "rating": 8,
                    "target": item["anime"],
                }

        report = import_shikimori_rates(
            session,
            user_id=user.id,
            external_user_id="77",
            adapter=Adapter(),
        )
        assert report.imported == 1
        title = session.scalar(select(Title).where(Title.title == "Тестовое аниме"))
        assert title is not None
        entry = session.scalar(
            select(LibraryEntry).where(LibraryEntry.title_id == title.id)
        )
        assert entry.progress_current is None
        assert entry.progress_total is None
        ext = session.scalar(
            select(ExternalTitle).where(ExternalTitle.external_id == "42")
        )
        assert ext is not None
        rating = session.scalar(
            select(UserExternalRating).where(
                UserExternalRating.external_title_id == ext.id
            )
        )
        assert rating.rating == 8


def test_import_reports_same_name_conflict_without_merging():
    with SessionLocal.begin() as session:
        user = User(username="conflict-user")
        session.add(user)
        session.flush()
        session.add(
            UserList(
                user_id=user.id,
                media_type=MediaType.ANIME,
                name="Watching",
                system_key="watching",
                is_system=True,
            )
        )
        session.add(Title(title="Same", media_type=MediaType.ANIME))
        session.flush()

        class Adapter:
            def fetch_user_rates(self, **kwargs):
                return [
                    {
                        "target_id": 9,
                        "status": "watching",
                        "score": 0,
                        "anime": {"id": 9, "name": "Same"},
                    }
                ]

            def _normalize_user_rate(self, item):
                return {
                    "external_id": "9",
                    "media_type": MediaType.ANIME,
                    "status": "watching",
                    "rating": 0,
                    "target": item["anime"],
                }

        report = import_shikimori_rates(
            session,
            user_id=user.id,
            external_user_id="1",
            adapter=Adapter(),
        )
        assert report.conflicts
        assert report.created_titles == 1
