from typing import Any

from fastapi import APIRouter

from src.webhook.judger import get_judger_infos

router = APIRouter(prefix="/judgers", tags=["user.judger"])


@router.get("", response_model=list[dict[str, Any]])
def list_judgers():
    return get_judger_infos()
