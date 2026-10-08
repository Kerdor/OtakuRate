import pytest

from otakurate.config import get_settings
from otakurate.database import SessionLocal
from otakurate.models import User
from otakurate.services.dev_user import get_dev_user


@pytest.fixture(autouse=True)
def enable_dev_user(monkeypatch):
    # Keep the test database configured as "test", but enable the dev-only service.
    monkeypatch.setattr(get_settings(), "environment", "dev")


def test_dev_user_is_created_and_reused():
    with SessionLocal() as session:
        first = get_dev_user(session)
        session.commit()
        first_id = first.id

    with SessionLocal() as session:
        second = get_dev_user(session)
        assert second.id == first_id
        assert second.username == "dev"


def test_dev_user_has_single_record():
    with SessionLocal() as session:
        get_dev_user(session)
        get_dev_user(session)
        assert session.query(User).filter_by(username="dev").count() == 1
