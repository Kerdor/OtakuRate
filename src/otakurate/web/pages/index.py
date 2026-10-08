import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy import select

from ...database import SessionLocal
from ...models import Title, UserRating
from ...rating import ANIME_CRITERIA, CRITERION_INFO, MANGA_CRITERIA

templates = Jinja2Templates(directory="src/otakurate/templates")
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


@router.get("/titles/new", response_class=HTMLResponse)
async def new_title(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="new_title.html",
        context={},
    )


@router.get("/rate", response_class=HTMLResponse)
async def rate(request: Request):
    media_type = request.query_params.get("type", "anime")
    if media_type not in {"anime", "manga"}:
        media_type = "anime"
    title = request.query_params.get("title", "Новый тайтл")
    criteria = ANIME_CRITERIA if media_type == "anime" else MANGA_CRITERIA
    rating_data = {
        "media_type": media_type,
        "title": title[:255],
        "criteria": {
            criterion.value: {
                "name": CRITERION_INFO[criterion].name,
                "description": CRITERION_INFO[criterion].description,
                "scores": CRITERION_INFO[criterion].score_descriptions,
                "weight": 1.0,
            }
            for criterion in criteria
        },
    }
    return templates.TemplateResponse(
        request=request,
        name="rating.html",
        context={"rating_data": json.dumps(rating_data, ensure_ascii=False), "title_id": request.query_params.get("title_id"), "user_id": request.query_params.get("user_id")},
    )

@router.get("/title/{title_id}", response_class=HTMLResponse)
async def title_card(request: Request, title_id: int):
    user_id_raw = request.query_params.get("user_id")
    user_id = int(user_id_raw) if user_id_raw and user_id_raw.isdigit() else None
    with SessionLocal() as session:
        title = session.get(Title, title_id)
        if title is None:
            raise HTTPException(status_code=404, detail="Title not found.")

        rating = None
        entry = None
        if user_id is not None:
            rating = session.scalar(select(UserRating).where(UserRating.user_id == user_id, UserRating.title_id == title.id))
            from ...models import LibraryEntry
            entry = session.scalar(select(LibraryEntry).where(LibraryEntry.user_id == user_id, LibraryEntry.title_id == title.id))

        return templates.TemplateResponse(
            request=request,
            name="title.html",
            context={"title": title, "rating": rating, "entry": entry, "user_id": user_id},
        )
