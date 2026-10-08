from sqlalchemy import select
from sqlalchemy.orm import Session

from ..domain.enums import MediaType
from ..models import LibraryEntry, Title, UserList


def get_user_lists(session: Session, *, user_id: int, media_type: MediaType) -> list[UserList]:
    return list(
        session.scalars(
            select(UserList)
            .where(
                UserList.user_id == user_id,
                UserList.media_type == media_type,
            )
            .order_by(UserList.is_system.desc(), UserList.name.asc(), UserList.id.asc())
        )
    )


def add_to_list(
    session: Session,
    *,
    user_id: int,
    title_id: int,
    list_id: int,
) -> LibraryEntry:
    user_list = session.scalar(
        select(UserList).where(
            UserList.id == list_id,
            UserList.user_id == user_id,
        )
    )
    if user_list is None:
        raise ValueError("List was not found.")

    title = session.get(Title, title_id)
    if title is None:
        raise ValueError("Title was not found.")
    if title.media_type != user_list.media_type:
        raise ValueError("List media type does not match the title.")

    entry = session.scalar(
        select(LibraryEntry).where(
            LibraryEntry.user_id == user_id,
            LibraryEntry.title_id == title_id,
        )
    )
    if entry is None:
        entry = LibraryEntry(
            user_id=user_id,
            title_id=title_id,
            list_id=user_list.id,
        )
        session.add(entry)
    else:
        entry.list_id = user_list.id

    session.flush()
    return entry


def get_entry(
    session: Session,
    *,
    user_id: int,
    title_id: int,
) -> LibraryEntry | None:
    return session.scalar(
        select(LibraryEntry).where(
            LibraryEntry.user_id == user_id,
            LibraryEntry.title_id == title_id,
        )
    )


def update_entry(
    session: Session,
    *,
    user_id: int,
    title_id: int,
    list_id: int | None = None,
    progress_current: int | None = None,
    progress_total: int | None = None,
    completed_at=None,
) -> LibraryEntry:
    entry = get_entry(session, user_id=user_id, title_id=title_id)
    if entry is None:
        raise ValueError("Library entry was not found.")

    if list_id is not None:
        user_list = session.scalar(
            select(UserList).where(
                UserList.id == list_id,
                UserList.user_id == user_id,
            )
        )
        if user_list is None or user_list.media_type != session.get(Title, title_id).media_type:
            raise ValueError("List was not found for this title.")
        entry.list_id = list_id

    if progress_current is not None and progress_current < 0:
        raise ValueError("Progress cannot be negative.")
    if progress_total is not None and progress_total <= 0:
        raise ValueError("Progress total must be positive.")
    if progress_current is not None and progress_total is not None and progress_current > progress_total:
        raise ValueError("Current progress cannot exceed total progress.")

    if progress_current is not None:
        entry.progress_current = progress_current
    if progress_total is not None:
        entry.progress_total = progress_total
    if completed_at is not None:
        entry.completed_at = completed_at

    session.flush()
    return entry
