from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ...database import SessionLocal
from ...models import User
from ...services.friends import can_view_section, get_friend_requests, get_friends
from ..api.dependencies import get_current_user

templates = Jinja2Templates(directory="src/otakurate/templates")
router = APIRouter()


@router.get("/friends", response_class=HTMLResponse)
async def friends_page(request: Request):
    with SessionLocal() as session:
        user = get_current_user(request, session)
        return templates.TemplateResponse(
            request=request, name="friends.html",
            context={"user": user, "friends": get_friends(session, user.id),
                     "incoming": get_friend_requests(session, user.id, incoming=True),
                     "outgoing": get_friend_requests(session, user.id, incoming=False)},
        )


@router.get("/users/{user_id}", response_class=HTMLResponse)
async def user_page(request: Request, user_id: int):
    with SessionLocal() as session:
        viewer = get_current_user(request, session)
        target = session.get(User, user_id)
        if target is not None and (not target.is_active or not can_view_section(session, viewer.id, target, "profile")):
            target = None
        return templates.TemplateResponse(
            request=request, name="user.html",
            context={"viewer": viewer, "target": target},
        )
