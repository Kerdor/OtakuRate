from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...services.auth import AuthError, authenticate_user, register_user
from .dependencies import get_current_user, get_session

router = APIRouter(prefix="/auth", tags=["auth"])


class CredentialsPayload(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=512)


@router.post("/register", response_model=dict, status_code=201)
def register(
    payload: CredentialsPayload,
    request: Request,
    session: Session = Depends(get_session),
):
    try:
        user = register_user(
            session,
            username=payload.username,
            password=payload.password,
        )
        session.commit()
    except AuthError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    request.session.clear()
    request.session["user_id"] = user.id
    return {"id": user.id, "username": user.username}


@router.post("/login", response_model=dict)
def login(
    payload: CredentialsPayload,
    request: Request,
    session: Session = Depends(get_session),
):
    user = authenticate_user(
        session,
        username=payload.username,
        password=payload.password,
    )
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    request.session.clear()
    request.session["user_id"] = user.id
    return {"id": user.id, "username": user.username}


@router.post("/logout", response_model=dict)
def logout(request: Request):
    request.session.clear()
    return {"ok": True}


@router.get("/me", response_model=dict)
def me(request: Request, session: Session = Depends(get_session)):
    user = get_current_user(request, session)
    return {"id": user.id, "username": user.username}
