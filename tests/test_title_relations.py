import pytest
from sqlalchemy.exc import IntegrityError

from otakurate.database import Base, SessionLocal
from otakurate.domain.enums import MediaType
from otakurate.models import Franchise, FranchiseTitle, Title, TitleRelation, TitleRelationType


def test_relation_models_are_registered():
    assert "title_relations" in Base.metadata.tables
    assert "franchises" in Base.metadata.tables
    assert "franchise_titles" in Base.metadata.tables


def test_anime_manga_relation_is_supported():
    with SessionLocal.begin() as session:
        anime = Title(title="Test Anime", media_type=MediaType.ANIME)
        manga = Title(title="Test Manga", media_type=MediaType.MANGA)
        session.add_all([anime, manga])
        session.flush()
        relation = TitleRelation(
            source_title_id=anime.id,
            target_title_id=manga.id,
            relation_type=TitleRelationType.ADAPTATION,
        )
        session.add(relation)
        session.flush()
        assert relation.id is not None


def test_season_relation_supports_order():
    with SessionLocal.begin() as session:
        season_1 = Title(title="Season 1", media_type=MediaType.ANIME)
        season_2 = Title(title="Season 2", media_type=MediaType.ANIME)
        session.add_all([season_1, season_2])
        session.flush()
        relation = TitleRelation(
            source_title_id=season_1.id,
            target_title_id=season_2.id,
            relation_type=TitleRelationType.SEASON,
            order_index=2,
        )
        session.add(relation)
        session.flush()
        assert relation.order_index == 2


def test_self_relation_is_forbidden():
    with pytest.raises(IntegrityError):
        with SessionLocal.begin() as session:
            title = Title(title="Self", media_type=MediaType.ANIME)
            session.add(title)
            session.flush()
            session.add(TitleRelation(
                source_title_id=title.id,
                target_title_id=title.id,
                relation_type=TitleRelationType.RELATED,
            ))
            session.flush()


def test_duplicate_relation_is_forbidden():
    with SessionLocal.begin() as session:
        first = Title(title="First", media_type=MediaType.ANIME)
        second = Title(title="Second", media_type=MediaType.ANIME)
        session.add_all([first, second])
        session.flush()
        session.add(TitleRelation(
            source_title_id=first.id,
            target_title_id=second.id,
            relation_type=TitleRelationType.SEQUEL,
        ))

    with pytest.raises(IntegrityError):
        with SessionLocal.begin() as session:
            session.add(TitleRelation(
                source_title_id=first.id,
                target_title_id=second.id,
                relation_type=TitleRelationType.SEQUEL,
            ))
            session.flush()


def test_title_can_belong_to_a_franchise():
    with SessionLocal.begin() as session:
        franchise = Franchise(name="Test Franchise")
        title = Title(title="Franchise Title", media_type=MediaType.ANIME)
        session.add_all([franchise, title])
        session.flush()
        membership = FranchiseTitle(
            franchise_id=franchise.id,
            title_id=title.id,
            order_index=1,
        )
        session.add(membership)
        session.flush()
        assert membership.id is not None
