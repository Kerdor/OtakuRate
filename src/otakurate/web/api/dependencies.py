from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from ...config import get_settings
from ...models import User
from ...services.dev_user import get_dev_user


def get_current_user(request: Request, session: Session) -> User:
    user_id = request.session.get("user_id")
    if user_id is not None:
        user = session.get(User, int(user_id))
        if user is not None and user.is_active:
            return user
        request.session.clear()

    if get_settings().environment == "dev":
        return get_dev_user(session)

    raise HTTPException(status_code=401, detail="Authentication required.")
