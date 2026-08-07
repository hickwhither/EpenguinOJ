from fastapi import APIRouter
router = APIRouter(prefix="/api", tags=["user"])

from .auth import router as auth_router
router.include_router(auth_router)

from .problem import router as problem_router
router.include_router(problem_router)

from .contest import router as contest_router
router.include_router(contest_router)

from .discord import router as discord_router
router.include_router(discord_router)
