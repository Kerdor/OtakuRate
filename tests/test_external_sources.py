import pytest
from sqlalchemy.exc import IntegrityError

from otakurate.database import Base, SessionLocal
from otakurate.domain.enums import MediaType
from otakurate.models import ExternalSource, ExternalTitle, Title, User, UserExternalAccount


def test_external_models_are_registered():
    assert "external_sources" in Base.metadata.tables
    assert "external_titles" in Base.metadata.tables
    assert "user_external_accounts" in Base.metadata.tables


def test_same_external_id_cannot_be_used_twice_for_one_source():
    with SessionLocal.begin() as session:
        source = ExternalSource(key="test", name="Test")
        session.add(source)
        session.flush()

        title = Title(title="Title", media_type=MediaType.ANIME)
        session.add(title)
        session.flush()

        session.add(ExternalTitle(
            title_id=title.id,
            source_id=source.id,
            external_id="123",
        ))

    with pytest.raises(IntegrityError):
        with SessionLocal.begin() as session:
            session.add(ExternalTitle(
                title_id=title.id,
                source_id=source.id,
                external_id="123",
            ))
            session.flush()


def test_one_user_has_one_connection_per_source():
    with SessionLocal.begin() as session:
        user = User(username="external-user")
        source = ExternalSource(key="account-test", name="Test")
        session.add_all([user, source])
        session.flush()

        session.add(UserExternalAccount(
            user_id=user.id,
            source_id=source.id,
        ))

    with pytest.raises(IntegrityError):
        with SessionLocal.begin() as session:
            session.add(UserExternalAccount(
                user_id=user.id,
                source_id=source.id,
            ))
            session.flush()
