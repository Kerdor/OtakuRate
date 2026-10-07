from datetime import datetime

from sqlalchemy import text

from otakurate.database import Base, SessionLocal
from otakurate.models import User


def test_user_model_is_registered():
    assert "users" in Base.metadata.tables


def test_user_can_be_created_with_defaults():
    with SessionLocal.begin() as session:
        user = User(username="test-user")
        session.add(user)
        session.flush()

        assert user.id is not None
        assert user.settings == {}
        assert isinstance(user.created_at, datetime)


def test_user_username_is_unique():
    with SessionLocal.begin() as session:
        session.add(User(username="unique-user"))

    with SessionLocal.begin() as session:
        session.add(User(username="unique-user"))
        try:
            session.flush()
        except Exception:
            return

    raise AssertionError("Duplicate usernames must be rejected.")
