from sqlalchemy import select
from sqlalchemy.orm import Session

from ..integrations.base import ExternalSearchResult
from ..models import ExternalSource, ExternalTitle, Title


def ensure_external_source(
    session: Session,
    *,
    key: str,
    name: str,
    base_url: str | None = None,
) -> ExternalSource:
    source = session.scalar(
        select(ExternalSource).where(ExternalSource.key == key)
    )
    if source is None:
        source = ExternalSource(key=key, name=name, base_url=base_url)
        session.add(source)
        session.flush()
    return source


def link_external_title(
    session: Session,
    *,
    title_id: int,
    source_key: str,
    result: ExternalSearchResult,
) -> ExternalTitle:
    title = session.get(Title, title_id)
    if title is None:
        raise ValueError("Title not found.")
    if title.media_type != result.media_type:
        raise ValueError("External title media type does not match Title.")

    source = session.scalar(
        select(ExternalSource).where(ExternalSource.key == source_key)
    )
    if source is None:
        raise ValueError("External source not found.")

    existing = session.scalar(
        select(ExternalTitle).where(
            ExternalTitle.source_id == source.id,
            ExternalTitle.external_id == result.external_id,
        )
    )
    if existing is not None:
        if existing.title_id != title_id:
            raise ValueError("External ID is already linked to another Title.")
        return existing

    external_title = ExternalTitle(
        title_id=title_id,
        source_id=source.id,
        external_id=result.external_id,
        url=result.url,
        media_type=result.media_type,
        external_title=result.title,
        alternative_titles=list(result.alternative_titles),
        extra_metadata=result.metadata,
    )
    session.add(external_title)
    session.flush()
    return external_title
