import os, secrets
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
security = HTTPBearer()
SECRET_KEY = os.getenv("SECRET_KEY")

def verify_secret_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Check valid SECRET_KEY for webhooks"""
    is_valid = secrets.compare_digest(credentials.credentials, SECRET_KEY)
    if not is_valid:
        raise HTTPException(403, "Forbidden: Invalid Secret Key")
    return True

router = APIRouter(tags=["webhook"], dependencies=[Depends(verify_secret_key)])

from .judger import router as judger_router
from .discord import router as discord_router
router.include_router(judger_router)
router.include_router(discord_router)