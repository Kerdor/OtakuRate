from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .web.api.router import router as api_router
from .web.pages.index import router as pages_router

settings = get_settings()

app = FastAPI(
    title="OtakuRate",
    debug=settings.debug,
)
app.mount("/static", StaticFiles(directory="src/otakurate/static"), name="static")
app.include_router(pages_router)
app.include_router(api_router)
