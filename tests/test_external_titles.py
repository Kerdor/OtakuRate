from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from otakurate.database import Base
from otakurate.domain.enums import MediaType
from otakurate.integrations.base import ExternalSearchResult
from otakurate.models import ExternalSource, Title
from otakurate.services.external_titles import ensure_external_source, link_external_title


def test_link_external_title():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        title = Title(title="Наруто", media_type=MediaType.ANIME)
        session.add(title)
        session.flush()

        ensure_external_source(
            session,
            key="shikimori",
            name="Shikimori",
            base_url="https://shikimori.one",
        )
        linked = link_external_title(
            session,
            title_id=title.id,
            source_key="shikimori",
            result=ExternalSearchResult(
                external_id="123",
                title="Наруто",
                media_type=MediaType.ANIME,
                url="https://shikimori.one/animes/123-naruto",
            ),
        )

        assert linked.external_id == "123"
        assert linked.title_id == title.id


def test_external_id_cannot_be_linked_to_another_title():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        first = Title(title="First", media_type=MediaType.ANIME)
        second = Title(title="Second", media_type=MediaType.ANIME)
        session.add_all([first, second])
        session.flush()

        ensure_external_source(session, key="shikimori", name="Shikimori")

        result = ExternalSearchResult(
            external_id="123",
            title="First",
            media_type=MediaType.ANIME,
        )
        link_external_title(
            session,
            title_id=first.id,
            source_key="shikimori",
            result=result,
        )

        try:
            link_external_title(
                session,
                title_id=second.id,
                source_key="shikimori",
                result=result,
            )
        except ValueError as exc:
            assert "already linked" in str(exc)
        else:
            raise AssertionError("Expected duplicate external ID to fail.")
