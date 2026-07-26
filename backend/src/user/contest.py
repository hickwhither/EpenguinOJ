from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import select, or_
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate

from src.database import SessionDep
from src.models import *
from src.dependencies.user import verify_auth
from src.dependencies.contest import *

# CONFIGURATIONS
router = APIRouter(prefix="/contest", tags=["user.contest"], dependencies=[Depends(verify_auth)])


# SCHEMAS
class ContestPublic(ContestPublic): is_registered: bool = False
class ContestView(ContestView): is_registered: bool = False

class SimpleContestRegistration(ContestRegistrationBase):
    user: "UserPublic"
    contest: "ContestPublic"


class ContestRegisterRequest(BaseModel):
    password: Optional[str] = None


# FUNCTIONS
def build_contest_is_registered(session: SessionDep, current_user: User):
    is_registered_subquery = (
        select(1)
        .where(
            ContestRegistration.contest_id == Contest.id,
            ContestRegistration.user_id == current_user.id
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
def get_ongoing_contests(
    session: SessionDep, 
    current_user: User = Depends(verify_auth)
):
    now = datetime.now()
    statement = (
        build_contest_is_registered(session, current_user)
        .where(
            Contest.start_time <= now,
            Contest.end_time >= now
        )
        .order_by(Contest.end_time.asc())
    )
    results = session.exec(statement).all()
    return transform_contest_with_is_registered(results)


@router.get("/upcoming", response_model=list[ContestPublic])
def get_upcoming_contests(
    session: SessionDep, 
    current_user: User = Depends(verify_auth)
):
    now = datetime.now()
    statement = (
        build_contest_is_registered(session, current_user)
        .where(Contest.start_time > now)
        .order_by(Contest.start_time.asc())
    )
    results = session.exec(statement).all()
    return transform_contest_with_is_registered(results)


@router.get("/ended", response_model=Page[ContestPublic])
def get_ended_contests(
    session: SessionDep,
    search: str | None = None
):
    now = datetime.now()
    statement = select(Contest).where(Contest.end_time < now)
    if search:
        search_filter = f"%{search.strip()}%"
        statement = statement.where(Contest.name.ilike(search_filter))
    statement = statement.order_by(Contest.end_time.desc())
    return paginate(session, statement)


@router.get("/{id}", response_model=ContestView)
def get_contest(
    session: SessionDep,
    id: str,
    current_user: User = Depends(verify_auth),
):
    contest_db = get_contest_or_404(session, id)
    running = is_contest_running(contest_db)
    is_participant = is_contest_participant(session, contest_db, current_user)
    contest_view = ContestView.model_validate(contest_db)
    contest_view.is_registered = is_participant
    if not running or not is_participant:
        contest_view.problems = None
    return contest_view


@router.post("/{id}/register")
def register_contest(
    session: SessionDep,
    id: str,
    payload: ContestRegisterRequest,
    current_user: User = Depends(verify_auth),
):
    contest = get_contest_or_404(session, id)
    ensure_registration_running(contest)
    if contest.password and payload.password != contest.password:
        raise HTTPException(403, "contest.wrongpassword")
    if not is_contest_participant(session, contest, current_user):
        session.add(ContestRegistration(contest_id=contest.id, user_id=current_user.id))
        session.commit()
    return


@router.get("/{id}/ranking", response_model=list[SimpleContestRegistration])
def get_contest(
    session: SessionDep,
    id: str,
    current_user: User = Depends(verify_auth),
):
    contest = get_contest_or_404(session, id)
    ensure_contest_running(contest)
    ensure_can_view_problem_contest(contest, current_user, session)
    return contest.registrations

