from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlmodel import select

from src.database import SessionDep
from src.dependencies import hash_password, verify_password
from src.dependencies.user import (
    create_auth,
    delete_auth,
    get_user_or_404,
    verify_auth,
)
from src.models import User, UserView

router = APIRouter(prefix="/auth", tags=["user.auth"])


# SCHEMAS
class CreateAccount(BaseModel):
    username: str
    email: EmailStr
    password: str


class PasswordForm(BaseModel):
    username: str
    password: str


class ProfileUpdate(BaseModel):
    nickname: str | None = None
    bio: str | None = None
    avatar_url: str | None = None


# ROUTERS
# @router.post("/signup", response_model=UserView, status_code=201)
# async def signup(request: Request, new_user: CreateAccount, session: SessionDep):
#     if await session.get(User, new_user.username):
#         raise HTTPException(400, "auth.exist_username")
    
#     existing_email = await session.exec(select(User).where(User.email == new_user.email))
#     if existing_email.first():
#         raise HTTPException(400, "auth.exist_email")

#     new_user.password = hash_password(new_user.password)
#     user_data = new_user.model_dump()
#     user = User(**user_data)
    
#     session.add(user)
#     await session.commit()
#     await session.refresh(user)

#     create_auth(request, user)
#     return user


@router.post("/signin", response_model=UserView)
async def signin(request: Request, session: SessionDep, payload: PasswordForm):
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