from sqlalchemy.orm import Session

from ..domain.enums import MediaType
from ..models import Title


def create_title(
    session: Session,
    *,
    title: str,
    media_type: MediaType,
) -> Title:
    name = title.strip()
    if not name:
        raise ValueError("Title cannot be empty.")
    if len(name) > 255:
        raise ValueError("Title is too long.")

    item = Title(
        title=name,
        media_type=media_type,
    )
    session.add(item)
    session.flush()
    return item
