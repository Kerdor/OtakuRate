from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ExternalTitle, Title


def find_title_by_external_id(
    session: Session,
    source_id: int,
    external_id: str,
) -> Title | None:
    statement = (
        select(Title)
        .join(ExternalTitle, ExternalTitle.title_id == Title.id)
        .where(
            ExternalTitle.source_id == source_id,
            ExternalTitle.external_id == external_id,
        )
    )
    return session.scalar(statement)


def should_merge_by_title_name(*, existing_title: Title, incoming_title: str) -> bool:
    """Title names alone are never sufficient for automatic merging."""
    return False
