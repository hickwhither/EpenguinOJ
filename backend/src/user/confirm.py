import os
import jwt
from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlmodel import select, or_

from src.database import SessionDep
from src.models import User
from src.dependencies.user import create_auth, get_user_or_404
from src.dependencies import hash_password, verify_password

# CONFIGURATION
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


# HELPER FUNCTIONS
def decode_discord_token(secret: str) -> str:
    """
    Decodes the JWT token and extracts the discord_id.
    """
    try:
        payload = jwt.decode(secret, SECRET_KEY, algorithms=[ALGORITHM])
        discord_id = payload.get("discord_id")
        if not discord_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="confirm.missing"
            )
        return discord_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="confirm.expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="confirm.invalid_token"
        )


# ROUTERS
@router.post("/check")
async def check_token(data: BaseConfirmRequest):
    """Validates the secret token."""
    decode_discord_token(data.secret)
    return {"message": "Token is valid"}


@router.post("/create-account", status_code=status.HTTP_201_CREATED)
async def confirm_create_account(
    request: Request,
    data: ConfirmCreateAccountRequest,
    session: SessionDep
):
    discord_id = decode_discord_token(data.secret)

    statement = select(User).where(
        or_(
            User.username == data.username,
            User.email == data.email,
            User.discord_id == discord_id
        )
    )
    existing_users = (await session.exec(statement)).all()

    for existing_user in existing_users:
        if existing_user.username == data.username:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "confirm.exist_username")
        if existing_user.email == data.email:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "confirm.exist_email")
        if existing_user.discord_id == discord_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "confirm.exist_discord_id")

    new_user = User(
        username=data.username,
        email=data.email,
        password=hash_password(data.password),
        discord_id=discord_id
    )
    
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    create_auth(request, new_user)
    return {"message": "Account created successfully"}


@router.post("/reset-password")
async def confirm_reset_password(
    request: Request,
    data: ConfirmChangePasswordRequest,
    session: SessionDep
):
    discord_id = decode_discord_token(data.secret)

    statement = select(User).where(User.discord_id == discord_id)
    user = (await session.exec(statement)).first()
    
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "confirm.invalid_discord_id")

    user.password = hash_password(data.password)
    session.add(user)
    await session.commit()
    
    create_auth(request, user)
    return {"message": "Password reset successfully"}


@router.post("/quick-login")
async def confirm_quick_login(
    request: Request,
    data: BaseConfirmRequest,
    session: SessionDep
):
    discord_id = decode_discord_token(data.secret)

    statement = select(User).where(User.discord_id == discord_id)
    user = (await session.exec(statement)).first()
    
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "confirm.invalid_discord_id")
    
    create_auth(request, user)
    return {"message": "Logged in successfully"}