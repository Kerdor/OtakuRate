import json

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ...database import SessionLocal
from ...models import Title
from ...services.profile import get_profile_summary, get_rating_settings
from ..api.dependencies import get_current_user

templates = Jinja2Templates(directory="src/otakurate/templates")
router = APIRouter()


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    with SessionLocal() as session:
        user = get_current_user(request, session)
        settings = user.settings or {}
        favorite_ids = settings.get("favorite_title_ids", [])
        favorites = list(session.query(Title).filter(Title.id.in_(favorite_ids)).all()) if favorite_ids else []
        return templates.TemplateResponse(
            request=request,
            name="profile.html",
            context={
                "user": user,
                "settings": settings,
                "visibility": settings.get("visibility", {"profile": "private", "library": "private", "ratings": "private"}),
                "favorites": favorites,
                "statistics": get_profile_summary(session, user.id),
                "rating_settings_json": json.dumps(get_rating_settings(session, user.id), ensure_ascii=False),
            },
        )
