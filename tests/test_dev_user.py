import pytest

from otakurate.database import SessionLocal
from otakurate.models import User
from otakurate.services.dev_user import get_dev_user


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
