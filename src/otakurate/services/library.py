from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Select, exists, func, nullslast, select
from sqlalchemy.orm import Session

from ..domain.enums import MediaType
from ..models import LibraryEntry, LibraryEntryTag, Title, UserRating, UserTag


class LibrarySort(StrEnum):
    ADDED_NEWEST = "added_newest"
    ADDED_OLDEST = "added_oldest"
    COMPLETED_NEWEST = "completed_newest"
    COMPLETED_OLDEST = "completed_oldest"
    TITLE_ASC = "title_asc"
    TITLE_DESC = "title_desc"
    RATING_HIGH = "rating_high"
    RATING_LOW = "rating_low"
    PROGRESS_HIGH = "progress_high"
    PROGRESS_LOW = "progress_low"
    UPDATED_NEWEST = "updated_newest"
    RANDOM = "random"


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
    sort: LibrarySort = LibrarySort.ADDED_NEWEST,
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

    sort_order = {
        LibrarySort.ADDED_NEWEST: (LibraryEntry.created_at.desc(), LibraryEntry.id.desc()),
        LibrarySort.ADDED_OLDEST: (LibraryEntry.created_at.asc(), LibraryEntry.id.asc()),
        LibrarySort.COMPLETED_NEWEST: (nullslast(LibraryEntry.completed_at.desc()), LibraryEntry.id.desc()),
        LibrarySort.COMPLETED_OLDEST: (nullslast(LibraryEntry.completed_at.asc()), LibraryEntry.id.asc()),
        LibrarySort.TITLE_ASC: (Title.title.asc(), LibraryEntry.id.asc()),
        LibrarySort.TITLE_DESC: (Title.title.desc(), LibraryEntry.id.desc()),
        LibrarySort.RATING_HIGH: (nullslast(UserRating.overall_rating.desc()), LibraryEntry.id.desc()),
        LibrarySort.RATING_LOW: (nullslast(UserRating.overall_rating.asc()), LibraryEntry.id.asc()),
        LibrarySort.PROGRESS_HIGH: (nullslast(LibraryEntry.progress_current.desc()), LibraryEntry.id.desc()),
        LibrarySort.PROGRESS_LOW: (nullslast(LibraryEntry.progress_current.asc()), LibraryEntry.id.asc()),
        LibrarySort.UPDATED_NEWEST: (LibraryEntry.updated_at.desc(), LibraryEntry.id.desc()),
    }

    if sort is LibrarySort.RANDOM:
        query = query.order_by(func.random())
    else:
        query = query.order_by(*sort_order[sort])

    return list(session.scalars(query))
