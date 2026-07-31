from src.utils import utcnow
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import apaginate
from pydantic import BaseModel
from sqlalchemy.orm import selectinload
from sqlmodel import SQLModel, func, select

from src.database import SessionDep
from src.dependencies.contest import (
    ensure_can_view_contest_content,
    ensure_registration_running,
    get_contest_or_404,
    is_contest_participant,
)
from src.dependencies.user import verify_auth
from src.models import *
from src.services.ranking import penalty_minutes

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


class ContestRegisterRequest(BaseModel):
    password: Optional[str] = None


class RankingProblem(SQLModel):
    id: int
    name: str
    display_order: int


class RankingUser(SQLModel):
    username: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    rank: Optional[str] = None


class ProblemResult(SQLModel):
    score: float
    max_score: float
    accepted: bool


class RankingEntry(SQLModel):
    rank: int
    user: "RankingUser"
    total_score: float
    penalty: float
    problem_results: dict[str, ProblemResult]


class ContestRankingView(SQLModel):
    contest_id: int
    problems: list[RankingProblem]
    ranking: list[RankingEntry]


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
    contest_view = ContestView.model_validate(contest_db)
    contest_view.is_registered = await is_contest_participant(session, contest_db, current_user)

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


@router.get("/{id}/ranking", response_model=ContestRankingView)
async def get_contest_ranking(
    session: SessionDep,
    id: str,
    current_user: User = Depends(verify_auth),
):
    contest = await get_contest_or_404(session, id)
    await ensure_can_view_contest_content(contest, current_user, session)

    problems_stmt = (
        select(Problem, ContestTask.display_order)
        .join(ContestTask, ContestTask.problem_id == Problem.id)
        .where(ContestTask.contest_id == contest.id)
        .order_by(ContestTask.display_order.asc(), Problem.id.asc())
    )
    problem_rows = (await session.exec(problems_stmt)).all()
    problems = [
        RankingProblem(id=p.id, name=p.name, display_order=order)
        for p, order in problem_rows
    ]

    max_scores_stmt = (
        select(Submission.problem_id, func.max(Submission.max_score))
        .where(
            Submission.contest_id == contest.id,
            Submission.status == "D",
        )
        .group_by(Submission.problem_id)
    )
    max_score_by_problem = {
        pid: (ms or 0.0) for pid, ms in (await session.exec(max_scores_stmt)).all()
    }

    regs_stmt = (
        select(ContestRegistration)
        .where(ContestRegistration.contest_id == contest.id)
        .options(selectinload(ContestRegistration.user))
    )
    regs = (await session.exec(regs_stmt)).all()

    raw = []
    for reg in regs:
        user = reg.user
        problem_results = {}
        for p in problems:
            score = float(reg.problem_scores.get(str(p.id), 0.0))
            max_score = max_score_by_problem.get(p.id, 0.0)
            problem_results[str(p.id)] = ProblemResult(
                score=score,
                max_score=max_score,
                accepted=bool(max_score) and score >= max_score,
            )
        username = user.username if user else ""
        raw.append(
            (
                reg.total_score,
                penalty_minutes(reg, contest),
                username,
                RankingEntry(
                    rank=0,
                    user=RankingUser(
                        username=username,
                        nickname=user.nickname if user else None,
                        avatar_url=user.avatar_url if user else None,
                        rank=user.rank if user else None,
                    ),
                    total_score=reg.total_score,
                    penalty=penalty_minutes(reg, contest),
                    problem_results=problem_results,
                ),
            )
        )

    raw.sort(key=lambda item: (-item[0], item[1], item[2].lower()))
    ranking = [entry for _, _, _, entry in raw]
    for i, entry in enumerate(ranking, start=1):
        entry.rank = i

    return ContestRankingView(contest_id=contest.id, problems=problems, ranking=ranking)

