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
class BaseConfirmRequest(BaseModel):
    token: str


class CreateAccount(BaseConfirmRequest):
    username: str
    password: str


class ResetPassword(BaseConfirmRequest):
    new_password: str


# CONFIRM ROUTERS
@router.post("/check")
async def check_token(data: BaseConfirmRequest):
    """Validates the secret token."""
    decode_discord_token(data.token)
    return {"message": "Token is valid"}


@router.post("/signup", status_code=201)
async def signup(request: Request, data: CreateAccount, session: SessionDep):
    discord_id = decode_discord_token(data.token)
    
    new_user = await create_account(session, data.username, data.password, discord_id)
    create_auth(request, new_user)
    return {"message": "Account created successfully"}


@router.post("/reset-password")
async def confirm_reset_password(request: Request, data: ResetPassword, session: SessionDep):
    discord_id = decode_discord_token(data.token)
    statement = select(User).where(User.discord_id == discord_id)
    user = (await session.exec(statement)).first()
    if not user:
        raise HTTPException(404, "confirm.invalid_discord_id")
    
    await reset_password(session, user, data.new_password)
    create_auth(request, user)
    return {"message": "Password reset successfully"}


@router.post("/quick-login")
async def confirm_quick_login(request: Request, data: BaseConfirmRequest, session: SessionDep):
    discord_id = decode_discord_token(data.token)
    statement = select(User).where(User.discord_id == discord_id)
    user = (await session.exec(statement)).first()
    if not user:
        raise HTTPException(404, "confirm.invalid_discord_id")

    create_auth(request, user)
    return {"message": "Logged in successfully"}

