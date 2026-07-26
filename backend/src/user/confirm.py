import os
import jwt
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, EmailStr
from sqlmodel import select

from src.database import SessionDep
from src.models import User
from src.dependencies.user import create_auth, get_user_or_404

# CONFIGURATION
from src.dependencies import hash_password, verify_password
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

router = APIRouter(prefix="/confirm", tags=["user.confirm"])


# SCHEMAS
class BaseConfirmRequest(BaseModel):
    secret: str


class ConfirmCreateAccountRequest(BaseConfirmRequest):
    username: str
    email: EmailStr
    password: str


class ConfirmChangePasswordRequest(BaseConfirmRequest):
    password: str


class PasswordForm(BaseModel):
    username: str
    password: str


# FUNCTIONS
def decode_discord_token(secret: str) -> str:
    """
    Decodes the JWT token and extracts the discord_id.
    - confirm.missing: Token payload is missing discord_id
    - confirm.expired: Token has expired
    - confirm.invalid: Invalid token
    """
    try:
        payload = jwt.decode(secret, SECRET_KEY, algorithms=[ALGORITHM])
        discord_id = payload.get("discord_id")
        if not discord_id:
            raise HTTPException(400, "confirm.missing")
        return discord_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(400, "confirm.expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "confirm.invalid_token")


# ROUTERS
@router.post("/check")
def check_token(data: BaseConfirmRequest):
    """Validates the secret token."""
    decode_discord_token(data.secret)
    return {"message": "Token is valid"}


@router.post("/create-account", status_code=201)
def confirm_create_account(
    request: Request,
    data: ConfirmCreateAccountRequest,
    session: SessionDep
):
    discord_id = decode_discord_token(data.secret)

    # Check for existing records
    if session.exec(select(User).where(User.username == data.username)).one_or_none():
        raise HTTPException(400, "confirm.exist_username")
    if session.exec(select(User).where(User.email == data.email)).one_or_none():
        raise HTTPException(400, "confirm.exist_email")
    if session.exec(select(User).where(User.discord_id == discord_id)).one_or_none():
        raise HTTPException(400, "confirm.exist_discord_id")
    new_user = User(
        username=data.username,
        email=data.email,
        password=hash_password(data.password),
        discord_id=discord_id
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    create_auth(request, new_user)


@router.post("/reset-password")
def confirm_reset_password(
    request: Request,
    data: ConfirmChangePasswordRequest,
    session: SessionDep
):
    discord_id = decode_discord_token(data.secret)
    user = session.exec(select(User).where(User.discord_id == discord_id)).first()
    if not user:
        raise HTTPException(400, "confirm.invalid_discord_id")

    user.password = hash_password(data.password)
    session.add(user)
    session.commit()
    
    create_auth(request, user)


@router.post("/quick-login")
def confirm_quick_login(
    request: Request,
    data: BaseConfirmRequest,
    session: SessionDep
):
    discord_id = decode_discord_token(data.secret)
    user = session.exec(select(User).where(User.discord_id == discord_id)).first()
    if not user:
        raise HTTPException(404, "confirm.invalid_discord_id")
    
    create_auth(request, user)

