from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Select, exists, select
from sqlalchemy.orm import Session

from ..domain.enums import MediaType
from ..models import LibraryEntry, LibraryEntryTag, Title, UserRating, UserTag


@dataclass(frozen=True)
class LibraryFilters:
    media_type: MediaType | None = None
    list_id: int | None = None
    min_rating: int | None = None
    max_rating: int | None = None
    has_progress: bool | None = None
    completed: bool | None = None
    has_notes: bool | None = None
    tag_ids: tuple[int, ...] = ()
    added_from: datetime | None = None
    added_to: datetime | None = None
    completed_from: datetime | None = None
    completed_to: datetime | None = None


def filter_library(
    session: Session,
    *,
    user_id: int,
    filters: LibraryFilters | None = None,
) -> list[LibraryEntry]:
    filters = filters or LibraryFilters()

    query: Select[tuple[LibraryEntry]] = (
        select(LibraryEntry)
        .join(Title, Title.id == LibraryEntry.title_id)
        .outerjoin(
            UserRating,
            (UserRating.user_id == user_id)
            & (UserRating.title_id == LibraryEntry.title_id),
        )
        .where(LibraryEntry.user_id == user_id)
        .order_by(LibraryEntry.created_at.desc(), LibraryEntry.id.desc())
    )

    if filters.media_type is not None:
        query = query.where(Title.media_type == filters.media_type)

    if filters.list_id is not None:
        query = query.where(LibraryEntry.list_id == filters.list_id)

    if filters.min_rating is not None:
        query = query.where(UserRating.overall_rating >= filters.min_rating)

    if filters.max_rating is not None:
        query = query.where(UserRating.overall_rating <= filters.max_rating)

    if filters.has_progress is True:
        query = query.where(LibraryEntry.progress_current.is_not(None))
    elif filters.has_progress is False:
        query = query.where(LibraryEntry.progress_current.is_(None))

    if filters.completed is True:
        query = query.where(LibraryEntry.completed_at.is_not(None))
    elif filters.completed is False:
        query = query.where(LibraryEntry.completed_at.is_(None))

    if filters.has_notes is True:
        query = query.where(
            LibraryEntry.notes.is_not(None),
            LibraryEntry.notes != "",
        )
    elif filters.has_notes is False:
        query = query.where(
            (LibraryEntry.notes.is_(None)) | (LibraryEntry.notes == ""),
        )

    for tag_id in filters.tag_ids:
        query = query.where(
            exists(
                select(LibraryEntryTag.library_entry_id)
                .join(UserTag, UserTag.id == LibraryEntryTag.tag_id)
                .where(
                    LibraryEntryTag.library_entry_id == LibraryEntry.id,
                    LibraryEntryTag.tag_id == tag_id,
                    UserTag.user_id == user_id,
                )
            )
        )

    if filters.added_from is not None:
        query = query.where(LibraryEntry.created_at >= filters.added_from)

    if filters.added_to is not None:
        query = query.where(LibraryEntry.created_at <= filters.added_to)

    if filters.completed_from is not None:
        query = query.where(LibraryEntry.completed_at >= filters.completed_from)

    if filters.completed_to is not None:
        query = query.where(LibraryEntry.completed_at <= filters.completed_to)

    return list(session.scalars(query))
