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
