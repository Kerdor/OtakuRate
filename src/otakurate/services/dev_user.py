from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import User


DEV_USERNAME = "dev"


def get_dev_user(session: Session) -> User:
    if get_settings().environment != "dev":
        raise ValueError("Development user is available only in dev environment.")

    user = session.scalar(select(User).where(User.username == DEV_USERNAME))
    if user is None:
        user = User(username=DEV_USERNAME)
        session.add(user)
        session.flush()
    return user
