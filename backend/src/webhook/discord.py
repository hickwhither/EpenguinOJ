from fastapi import APIRouter
from pydantic import BaseModel
from sqlmodel import select

from src.database import SessionDep
from src.models.user import User
from src.services.user import encode_discord_token

router = APIRouter(prefix="/discord", tags=["webhook.discord"])


class VerifyCreateRequest(BaseModel):
    discord_id: str


@router.get("/user")
async def is_user_exists(session: SessionDep, discord_id: str):
    user = (await session.exec(select(User).where(User.discord_id == discord_id))).first()
    return user is not None


@router.post("/create")
def create_verify(data: VerifyCreateRequest):
    return encode_discord_token(data.discord_id)
