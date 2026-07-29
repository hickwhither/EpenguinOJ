import os, jwt
from datetime import *
from fastapi import APIRouter
from pydantic import BaseModel, EmailStr

# CONFIGURATIONS
from pwdlib import PasswordHash
pwd = PasswordHash.recommended()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

router = APIRouter(prefix="/discord", tags=["webhook.discord"])

# -- SCHEMAS --
from src.database import SessionDep
from src.models.user import User
from sqlmodel import select

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class VerifyCreateRequest(BaseModel):   
    discord_id: str

# -- ROUTERS --
@router.get("/user")
async def is_user_exists(session: SessionDep, discord_id: str):
    user = (await session.exec(select(User).where(User.discord_id == discord_id))).first()
    return user is not None

@router.post("/create")
def create_verify(data: VerifyCreateRequest):
    expire = datetime.now() + timedelta(minutes=5)
    payload = {
        "discord_id": data.discord_id,
        "exp": expire
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

