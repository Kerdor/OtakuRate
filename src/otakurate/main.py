from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .config import get_settings
from .web.api.auth import router as auth_router
from .web.api.router import router as api_router, title_search_router
from .web.pages.index import router as pages_router

settings = get_settings()

app = FastAPI(
    title="OtakuRate",
    debug=settings.debug,
)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret or "",
    session_cookie="otakurate_session",
    https_only=settings.environment == "prod",
    same_site="lax",
)
app.mount("/static", StaticFiles(directory="src/otakurate/static"), name="static")
app.include_router(pages_router)
app.include_router(api_router)
app.include_router(auth_router)
app.include_router(title_search_router)
