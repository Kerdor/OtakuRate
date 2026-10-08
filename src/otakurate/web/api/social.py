from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...models import LibraryEntry, Title, User, UserRating
from ...services.friends import (
    can_view_section, get_friend_requests, get_friends, get_visibility,
    remove_friend, respond_to_friend_request, send_friend_request,
)
from .dependencies import get_current_user, get_session

router = APIRouter(tags=["social"])


def _user_summary(user: User) -> dict:
    return {"id": user.id, "username": user.username, "display_name": (user.settings or {}).get("display_name") or user.username}


@router.get("/friends", response_model=list[dict])
def friends(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    return [_user_summary(friend) for friend in get_friends(session, user.id)]


@router.get("/friends/requests", response_model=dict)
def friend_requests(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    return {"incoming": get_friend_requests(session, user.id, incoming=True), "outgoing": get_friend_requests(session, user.id, incoming=False)}


@router.post("/friends/requests/{user_id}", response_model=dict, status_code=201)
def create_friend_request(user_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    try:
        request = send_friend_request(session, requester=user, addressee_id=user_id)
        session.commit()
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"request_id": request.id, "status": request.status.value}


@router.post("/friends/requests/{request_id}/accept", response_model=dict)
def accept_friend_request(request_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    try:
        request = respond_to_friend_request(session, request_id=request_id, user_id=user.id, accept=True)
        session.commit()
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"request_id": request.id, "status": request.status.value}


@router.post("/friends/requests/{request_id}/reject", response_model=dict)
def reject_friend_request(request_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    try:
        request = respond_to_friend_request(session, request_id=request_id, user_id=user.id, accept=False)
        session.commit()
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"request_id": request.id, "status": request.status.value}


@router.delete("/friends/{friend_id}", response_model=dict)
def delete_friend(friend_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    try:
        remove_friend(session, user_id=user.id, friend_id=friend_id)
        session.commit()
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"removed": True}


@router.get("/users/{user_id}/profile", response_model=dict)
def user_profile(user_id: int, session: Session = Depends(get_session), viewer: User = Depends(get_current_user)):
    target = session.get(User, user_id)
    if target is None or not target.is_active:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")
    if not can_view_section(session, viewer.id, target, "profile"):
        raise HTTPException(status_code=403, detail="Профиль скрыт настройками приватности.")
    result = {"user": _user_summary(target), "visibility": get_visibility(target)}
    if can_view_section(session, viewer.id, target, "library"):
        entries = session.execute(
            select(LibraryEntry, Title).join(Title, Title.id == LibraryEntry.title_id)
            .where(LibraryEntry.user_id == target.id).order_by(Title.title)
        ).all()
        result["library"] = [
            {"title_id": title.id, "title": title.title, "media_type": title.media_type.value, "progress_current": entry.progress_current, "progress_total": entry.progress_total}
            for entry, title in entries
        ]
    else:
        result["library"] = None
    if can_view_section(session, viewer.id, target, "ratings"):
        ratings = session.execute(
            select(UserRating, Title).join(Title, Title.id == UserRating.title_id)
            .where(UserRating.user_id == target.id).order_by(Title.title)
        ).all()
        result["ratings"] = [
            {"title_id": title.id, "title": title.title, "media_type": title.media_type.value, "overall_rating": rating.overall_rating}
            for rating, title in ratings
        ]
    else:
        result["ratings"] = None
    return result


@router.get("/users/{user_id}/compare", response_model=dict)
def compare_user(user_id: int, session: Session = Depends(get_session), viewer: User = Depends(get_current_user)):
    target = session.get(User, user_id)
    if target is None or not target.is_active:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")
    if not can_view_section(session, viewer.id, target, "profile"):
        raise HTTPException(status_code=403, detail="Профиль скрыт настройками приватности.")
    own_library_allowed = can_view_section(session, viewer.id, viewer, "library")
    target_library_allowed = can_view_section(session, viewer.id, target, "library")
    own_ratings_allowed = can_view_section(session, viewer.id, viewer, "ratings")
    target_ratings_allowed = can_view_section(session, viewer.id, target, "ratings")
    if not own_library_allowed or not target_library_allowed:
        shared = None
    else:
        own_entries = session.execute(select(LibraryEntry.title_id, LibraryEntry.list_id).where(LibraryEntry.user_id == viewer.id)).all()
        target_entries = session.execute(select(LibraryEntry.title_id, LibraryEntry.list_id).where(LibraryEntry.user_id == target.id)).all()
        own_ids = {row.title_id: row.list_id for row in own_entries}
        target_ids = {row.title_id: row.list_id for row in target_entries}
        common_ids = set(own_ids) & set(target_ids)
        titles = session.scalars(select(Title).where(Title.id.in_(common_ids)).order_by(Title.title)).all() if common_ids else []
        shared = [{"title_id": title.id, "title": title.title, "media_type": title.media_type.value, "my_list_id": own_ids[title.id], "friend_list_id": target_ids[title.id]} for title in titles]
    differences = None
    if own_ratings_allowed and target_ratings_allowed:
        own_ratings = {row.title_id: row.overall_rating for row in session.scalars(select(UserRating).where(UserRating.user_id == viewer.id)).all()}
        target_ratings = {row.title_id: row.overall_rating for row in session.scalars(select(UserRating).where(UserRating.user_id == target.id)).all()}
        common_rated = set(own_ratings) & set(target_ratings)
        titles = session.scalars(select(Title).where(Title.id.in_(common_rated)).order_by(Title.title)).all() if common_rated else []
        differences = [{"title_id": title.id, "title": title.title, "media_type": title.media_type.value, "my_rating": own_ratings[title.id], "friend_rating": target_ratings[title.id], "difference": own_ratings[title.id] - target_ratings[title.id]} for title in titles]
    return {"user": _user_summary(target), "shared_titles": shared, "rating_differences": differences}


@router.get("/users/search", response_model=list[dict])
def search_users(query: str, limit: int = 20, session: Session = Depends(get_session), viewer: User = Depends(get_current_user)):
    limit = max(1, min(limit, 50))
    normalized = query.strip().lstrip("@")
    if len(normalized) < 2:
        return []
    users = session.scalars(select(User).where(User.is_active.is_(True), User.id != viewer.id, User.username.ilike(f"%{normalized}%")).order_by(User.username).limit(limit)).all()
    return [{"id": user.id, "username": user.username, "display_name": (user.settings or {}).get("display_name") or user.username} for user in users]
