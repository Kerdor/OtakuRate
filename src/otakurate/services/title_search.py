from sqlalchemy import select
from sqlalchemy.orm import Session

from ..domain.enums import MediaType
from ..models import Title


def search_titles(
    session: Session,
    *,
    query: str,
    media_type: MediaType | None = None,
    limit: int = 20,
) -> list[Title]:
    search = query.strip()
    if not search:
        return []

    limit = max(1, min(limit, 50))
    statement = select(Title).where(Title.title.ilike(f"%{search}%"))

    if media_type is not None:
        statement = statement.where(Title.media_type == media_type)

    statement = statement.order_by(Title.title.asc(), Title.id.asc()).limit(limit)
    return list(session.scalars(statement))
