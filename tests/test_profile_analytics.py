from datetime import datetime, timezone

from otakurate.database import SessionLocal
from otakurate.domain.enums import MediaType
from otakurate.models import Title, User, UserRating
from otakurate.services.profile import get_profile_summary


def test_profile_analytics_calculate_rating_distribution_criteria_genres_and_timeline():
    with SessionLocal() as session:
        user = User(username="analytics-user")
        session.add(user)
        session.flush()

        titles = [
            Title(title="Anime One", media_type=MediaType.ANIME, genres=["Fantasy", "Action"]),
            Title(title="Anime Two", media_type=MediaType.ANIME, genres=["Fantasy"]),
            Title(title="Manga One", media_type=MediaType.MANGA, genres=["Drama"]),
            Title(title="Anime Three", media_type=MediaType.ANIME, genres=["Action"]),
        ]
        session.add_all(titles)
        session.flush()

        session.add_all([
            UserRating(
                user_id=user.id, title_id=titles[0].id, overall_rating=8,
                criteria_values={"story": 8}, rating_profile_version=1,
                created_at=datetime(2026, 1, 5, tzinfo=timezone.utc),
            ),
            UserRating(
                user_id=user.id, title_id=titles[1].id, overall_rating=10,
                criteria_values={"story": 10}, rating_profile_version=1,
                created_at=datetime(2026, 2, 10, tzinfo=timezone.utc),
            ),
            UserRating(
                user_id=user.id, title_id=titles[2].id, overall_rating=6,
                criteria_values={"story": 6}, rating_profile_version=1,
                created_at=datetime(2026, 1, 15, tzinfo=timezone.utc),
            ),
            UserRating(
                user_id=user.id, title_id=titles[3].id, overall_rating=8,
                criteria_values={"story": 8}, rating_profile_version=1,
                created_at=datetime(2026, 1, 25, tzinfo=timezone.utc),
            ),
        ])
        session.commit()

        summary = get_profile_summary(session, user.id)

        assert summary["rating_count"] == 4
        assert summary["average_rating"] == 8.0
        assert summary["anime_rating_count"] == 3
        assert summary["manga_rating_count"] == 1

        distribution = {item["rating"]: item for item in summary["rating_distribution"]}
        assert len(distribution) == 10
        assert distribution[8]["count"] == 2
        assert distribution[8]["percentage"] == 100
        assert distribution[6]["count"] == 1
        assert distribution[6]["percentage"] == 50
        assert distribution[9]["count"] == 0

        criteria = summary["criteria_averages"]
        anime_story = next(item for item in criteria["anime"] if item["key"] == "story")
        manga_story = next(item for item in criteria["manga"] if item["key"] == "story")
        assert anime_story["average"] == 8.67
        assert anime_story["count"] == 3
        assert manga_story["average"] == 6.0
        assert manga_story["count"] == 1

        genres = {item["name"]: item for item in summary["favorite_genres"]}
        assert genres["Fantasy"]["average"] == 9.0
        assert genres["Fantasy"]["count"] == 2
        assert genres["Action"]["average"] == 8.0
        assert genres["Action"]["count"] == 2

        assert summary["rating_timeline"] == [
            {
                "month": "2026-01",
                "label": "01.2026",
                "average": 7.33,
                "count": 3,
                "percentage": 73,
            },
            {
                "month": "2026-02",
                "label": "02.2026",
                "average": 10.0,
                "count": 1,
                "percentage": 100,
            },
        ]


def test_profile_analytics_return_empty_states_without_ratings():
    with SessionLocal() as session:
        user = User(username="analytics-empty-user")
        session.add(user)
        session.commit()

        summary = get_profile_summary(session, user.id)

        assert summary["rating_count"] == 0
        assert summary["average_rating"] is None
        assert summary["rating_distribution"] == [
            {"rating": rating, "count": 0, "percentage": 0}
            for rating in range(1, 11)
        ]
        assert summary["favorite_genres"] == []
        assert summary["rating_timeline"] == []
        assert all(
            item["average"] is None and item["count"] == 0
            for media_type in ("anime", "manga")
            for item in summary["criteria_averages"][media_type]
        )
