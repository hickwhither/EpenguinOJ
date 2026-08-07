import jwt
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlmodel import select

from src.models.user import User
from src.database import SessionDep
from src.models import UserView
from src.services.user import (
    decode_discord_token,
    create_account,
    reset_password,
    get_user_or_404,
    create_auth,
    delete_auth,
    verify_auth,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["user.auth"])


# SCHEMAS
class SigninForm(BaseModel):
    username: str
    password: str


class ProfileUpdate(BaseModel):
    nickname: str | None = None
    bio: str | None = None
    avatar_url: str | None = None


# ROUTERS
@router.post("/signin", response_model=UserView)
async def signin(request: Request, session: SessionDep, payload: SigninForm):
    user = await get_user_or_404(session, payload.username)

    if not verify_password(payload.password, user.password):
        raise HTTPException(400, "auth.wrongpassword")

    create_auth(request, user)
    return user


@router.post("/signout")
async def signout(request: Request):
    delete_auth(request)
    return {"message": "Success"}


@router.get("/profile", response_model=UserView)
@router.get("/profile/{username}", response_model=UserView)
async def profile(request: Request, session: SessionDep, username: str | None = None):
    if not username:
        return await verify_auth(request, session)
    return await get_user_or_404(session, username)


@router.patch("/profile", response_model=UserView)
async def update_profile(request: Request, session: SessionDep, payload: ProfileUpdate):
    user = await verify_auth(request, session)
    update_data = payload.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
