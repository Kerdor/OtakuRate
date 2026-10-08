from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..models import FriendRequest, FriendRequestStatus, User


def are_friends(session: Session, first_user_id: int, second_user_id: int) -> bool:
    if first_user_id == second_user_id:
        return True
    return session.scalar(
        select(FriendRequest.id).where(
            FriendRequest.status == FriendRequestStatus.ACCEPTED,
            or_(
                (FriendRequest.requester_id == first_user_id) & (FriendRequest.addressee_id == second_user_id),
                (FriendRequest.requester_id == second_user_id) & (FriendRequest.addressee_id == first_user_id),
            ),
        ).limit(1)
    ) is not None


def send_friend_request(session: Session, *, requester: User, addressee_id: int) -> FriendRequest:
    if requester.id == addressee_id:
        raise ValueError("Нельзя добавить в друзья самого себя.")
    addressee = session.get(User, addressee_id)
    if addressee is None or not addressee.is_active:
        raise ValueError("Пользователь не найден.")
    if are_friends(session, requester.id, addressee_id):
        raise ValueError("Вы уже друзья.")
    existing = session.scalar(
        select(FriendRequest).where(
            or_(
                (FriendRequest.requester_id == requester.id) & (FriendRequest.addressee_id == addressee_id),
                (FriendRequest.requester_id == addressee_id) & (FriendRequest.addressee_id == requester.id),
            )
        )
    )
    if existing is not None:
        if existing.status == FriendRequestStatus.PENDING:
            raise ValueError("Запрос в друзья уже ожидает ответа.")
        existing.requester_id = requester.id
        existing.addressee_id = addressee_id
        existing.status = FriendRequestStatus.PENDING
        session.flush()
        return existing
    request = FriendRequest(requester_id=requester.id, addressee_id=addressee_id)
    session.add(request)
    session.flush()
    return request


def respond_to_friend_request(
    session: Session, *, request_id: int, user_id: int, accept: bool
) -> FriendRequest:
    request = session.get(FriendRequest, request_id)
    if request is None or request.addressee_id != user_id:
        raise ValueError("Запрос не найден.")
    if request.status != FriendRequestStatus.PENDING:
        raise ValueError("Запрос уже обработан.")
    request.status = FriendRequestStatus.ACCEPTED if accept else FriendRequestStatus.REJECTED
    session.flush()
    return request


def remove_friend(session: Session, *, user_id: int, friend_id: int) -> None:
    request = session.scalar(
        select(FriendRequest).where(
            FriendRequest.status == FriendRequestStatus.ACCEPTED,
            or_(
                (FriendRequest.requester_id == user_id) & (FriendRequest.addressee_id == friend_id),
                (FriendRequest.requester_id == friend_id) & (FriendRequest.addressee_id == user_id),
            ),
        )
    )
    if request is None:
        raise ValueError("Пользователь не находится в списке друзей.")
    session.delete(request)
    session.flush()


def get_friends(session: Session, user_id: int) -> list[User]:
    rows = session.scalars(
        select(FriendRequest).where(
            FriendRequest.status == FriendRequestStatus.ACCEPTED,
            or_(FriendRequest.requester_id == user_id, FriendRequest.addressee_id == user_id),
        ).order_by(FriendRequest.updated_at.desc())
    ).all()
    friend_ids = [
        row.addressee_id if row.requester_id == user_id else row.requester_id
        for row in rows
    ]
    return list(session.scalars(select(User).where(User.id.in_(friend_ids), User.is_active.is_(True)))) if friend_ids else []


def get_friend_requests(session: Session, user_id: int, *, incoming: bool) -> list[dict]:
    field = FriendRequest.addressee_id if incoming else FriendRequest.requester_id
    rows = session.scalars(
        select(FriendRequest).where(field == user_id, FriendRequest.status == FriendRequestStatus.PENDING)
        .order_by(FriendRequest.created_at.desc())
    ).all()
    result = []
    for request in rows:
        other_id = request.requester_id if incoming else request.addressee_id
        other = session.get(User, other_id)
        if other is not None and other.is_active:
            result.append({"request_id": request.id, "user_id": other.id, "username": other.username, "created_at": request.created_at.isoformat()})
    return result


def get_visibility(user: User) -> dict[str, str]:
    configured = (user.settings or {}).get("visibility", {})
    return {
        "profile": configured.get("profile", "private"),
        "library": configured.get("library", "private"),
        "ratings": configured.get("ratings", "private"),
    }


def can_view_section(session: Session, viewer_id: int, target: User, section: str) -> bool:
    if viewer_id == target.id:
        return True
    visibility = get_visibility(target).get(section, "private")
    if visibility == "public":
        return True
    if visibility == "friends":
        return are_friends(session, viewer_id, target.id)
    return False
