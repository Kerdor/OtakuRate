import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ...database import SessionLocal
from ...models import Title
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
        context={"rating_data": json.dumps(rating_data, ensure_ascii=False)},
    )

@router.get("/title/{title_id}", response_class=HTMLResponse)
async def title_card(request: Request, title_id: int):
    with SessionLocal() as session:
        title = session.get(Title, title_id)
        if title is None:
            raise HTTPException(status_code=404, detail="Title not found.")

        return templates.TemplateResponse(
            request=request,
            name="title.html",
            context={"title": title},
        )
