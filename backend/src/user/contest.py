from src.utils import utcnow
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import apaginate
from pydantic import BaseModel
from sqlmodel import select

from src.database import SessionDep
from src.dependencies.contest import (
    ensure_can_view_problem_contest,
    ensure_contest_running,
    ensure_registration_running,
    get_contest_or_404,
    is_contest_participant,
    is_contest_running,
)
from src.dependencies.user import verify_auth
from src.models import *

# CONFIGURATIONS
router = APIRouter(
    prefix="/contest",
    tags=["user.contest"],
    dependencies=[Depends(verify_auth)],
)


# SCHEMAS
class ContestPublic(ContestPublic):
    is_registered: bool = False


class ContestView(ContestView):
    is_registered: bool = False


class SimpleContestRegistration(ContestRegistrationBase):
    user: "UserPublic"
    contest: "ContestPublic"


class ContestRegisterRequest(BaseModel):
    password: Optional[str] = None


# FUNCTIONS
def build_contest_is_registered(current_user: User):
    is_registered_subquery = (
        select(1)
        .where(
            ContestRegistration.contest_id == Contest.id,
            ContestRegistration.user_id == current_user.id,
        )
        .exists()
        .label("is_registered")
    )
    return select(Contest, is_registered_subquery)


def transform_contest_with_is_registered(results) -> list[ContestPublic]:
    items = []
    for contest, is_reg in results:
        contest_data = contest.model_dump()
        contest_data["is_registered"] = bool(is_reg)
        items.append(ContestPublic(**contest_data))
    return items


# ROUTERS
@router.get("/ongoing", response_model=list[ContestPublic])
async def get_ongoing_contests(
    session: SessionDep, current_user: User = Depends(verify_auth)
):
    now = utcnow()
    statement = (
        build_contest_is_registered(current_user)
        .where(Contest.start_time <= now, Contest.end_time >= now)
        .order_by(Contest.end_time.asc())
    )
    results = (await session.exec(statement)).all()
    return transform_contest_with_is_registered(results)


@router.get("/upcoming", response_model=list[ContestPublic])
async def get_upcoming_contests(
    session: SessionDep, current_user: User = Depends(verify_auth)
):
    now = utcnow()
    statement = (
        build_contest_is_registered(current_user)
        .where(Contest.start_time > now)
        .order_by(Contest.start_time.asc())
    )
    results = (await session.exec(statement)).all()
    return transform_contest_with_is_registered(results)


@router.get("/ended", response_model=Page[ContestPublic])
async def get_ended_contests(session: SessionDep, search: str | None = None):
    now = utcnow()
    statement = select(Contest).where(Contest.end_time < now)
    if search:
        search_filter = f"%{search.strip()}%"
        statement = statement.where(Contest.name.ilike(search_filter))
    statement = statement.order_by(Contest.end_time.desc())

    return await apaginate(session, statement)


@router.get("/{id}", response_model=ContestView)
async def get_contest(
    session: SessionDep,
    id: str,
    current_user: User = Depends(verify_auth),
):
    contest_db = await get_contest_or_404(session, id)
    running = is_contest_running(contest_db)
    is_participant = await is_contest_participant(session, contest_db, current_user)

    contest_view = ContestView.model_validate(contest_db)
    contest_view.is_registered = is_participant

    if not running or not is_participant:
        contest_view.problems = None

    return contest_view


@router.post("/{id}/register")
async def register_contest(
    session: SessionDep,
    id: str,
    payload: ContestRegisterRequest,
    current_user: User = Depends(verify_auth),
):
    contest = await get_contest_or_404(session, id)
    ensure_registration_running(contest)

    if contest.password and payload.password != contest.password:
        raise HTTPException(403, "contest.wrongpassword")

    if not await is_contest_participant(session, contest, current_user):
        session.add(
            ContestRegistration(contest_id=contest.id, user_id=current_user.id)
        )
        await session.commit()

    return {"message": "Registered successfully"}


@router.get("/{id}/ranking", response_model=list[SimpleContestRegistration])
async def get_contest_ranking(
    session: SessionDep,
    id: str,
    current_user: User = Depends(verify_auth),
):
    contest = await get_contest_or_404(session, id)
    ensure_contest_running(contest)
    await ensure_can_view_problem_contest(contest, current_user, session)

    # Trong Async, truy cập relationship lazy load cần lưu ý.
    # Nếu trong Model đã khai báo relationship(lazy="selectin"), gọi trực tiếp OK:
    # AI bao vay chu sqlmodel co dau hehe
    return contest.registrations

