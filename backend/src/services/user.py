import os
import jwt
from sqlite3 import IntegrityError
from pydantic import BaseModel
from sqlmodel import select
from fastapi import HTTPException, Request
from pwdlib import PasswordHash

from src.database import SessionDep
from src.models import User
from src.services.timing import utcnow

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

pwd = PasswordHash.recommended()


async def get_user_or_404(session: SessionDep, username: str) -> User:
    statement = select(User).where(User.username == username)
    results = await session.exec(statement)
    user = results.one_or_none()
    if not user:
        raise HTTPException(404, "user.notfound")
    return user


async def create_account(session: SessionDep, username: str, password: str, discord_id: str) -> User:
    statement = select(User).where(User.username == username)
    existing_user = (await session.exec(statement)).one_or_none()
    if existing_user:
        raise HTTPException(400, "confirm.exist_username")
    new_user = User(
        username=username,
        password=hash_password(password),
        discord_id=discord_id
    )
    session.add(new_user)
    try:
        await session.commit()
        await session.refresh(new_user)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(400, "confirm.exist_username")
    return new_user


async def reset_password(session: SessionDep, user: User, new_password: str):
    user.password = hash_password(new_password)
    session.add(user)
    await session.commit()
    await session.refresh(user)


def hash_password(password: str | bytes) -> str:
    return pwd.hash(password)


def verify_password(password: str | bytes, hash: str | bytes) -> bool:
    return pwd.verify(password, hash)


def encode_discord_token(discord_id: str) -> str:
    payload = {"discord_id": discord_id, "exp": utcnow() + 300}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_discord_token(secret: str) -> str:
    """Decodes the JWT token and extracts the discord_id."""
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


# Session auth
def create_auth(request: Request, user: User):
    request.session["id"] = user.id


def delete_auth(request: Request):
    request.session.pop("id", None)


async def verify_auth(request: Request, session: SessionDep) -> User:
    id = request.session.get("id")
    if not id:
        raise HTTPException(401, "user.not_authenticated")
    user = await session.get(User, id)
    if not user:
        raise HTTPException(401, "user.not_authenticated")
    return user
