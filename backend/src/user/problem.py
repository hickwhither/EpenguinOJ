import json
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import apaginate
from pydantic import BaseModel
from sqlalchemy import case
from sqlalchemy.orm import selectinload
from sqlmodel import or_, select

from src.database import SessionDep
from src.services.contest import (
    ensure_can_view_contest_content,
    ensure_can_view_problem_contest,
    ensure_contest_running,
    get_contest_or_404,
    get_contest_registration,
)
from src.services.user import get_user_or_404
from src.models import (
    ContestRegistration,
    Problem,
    ProblemPublic,
    ProblemView,
    Submission,
    SubmissionListOut,
    SubmissionDetailOut,
    User,
)
from src.services.user import verify_auth
from src.services.redis_sync import sync_problem_to_redis
from src.services.timing import utcnow

# CONFIGURATION
router = APIRouter(tags=["user.problem"], dependencies=[Depends(verify_auth)])


# SCHEMAS
class SubmissionCreate(BaseModel):
    language: str
    source: str


# FUNCTIONS
async def get_problem_or_404(session: SessionDep, id: str) -> Problem:
    problem = await session.get(Problem, id)
    if not problem:
        raise HTTPException(404, "problem.notfound")
    return problem


# ROUTERS
@router.get("/problems", response_model=Page[ProblemPublic])
async def get_list_problem(
    session: SessionDep,
    search: str | None = None,
):
    query = select(Problem).where(Problem.is_public == True)
    if search:
        search_filter = f"%{search.strip()}%"
        query = query.where(or_(Problem.name.ilike(search_filter), Problem.statement.ilike(search_filter)))
    query = query.order_by(Problem.id.desc())
    return await apaginate(session, query)


@router.get("/problem", response_model=ProblemView)
async def get_problem(
    session: SessionDep,
    problem_id: str,
    current_user: User = Depends(verify_auth),
):
    problem = await get_problem_or_404(session, problem_id)
    if problem.contest:
        await ensure_can_view_contest_content(problem.contest, current_user, session)
        return problem

    if not problem.is_public:
        raise HTTPException(403, "problem.forbidden")
    return problem


@router.post("/submit_code", status_code=201)
async def submit_code(
    request: Request,
    session: SessionDep,
    submit_form: SubmissionCreate,
    problem_id: str,
    contest_id: str | None = None,
    current_user: User = Depends(verify_auth),
):
    problem = await get_problem_or_404(session, problem_id)
    contest = None
    contest_registration = None

    if contest_id:
        contest = await get_contest_or_404(session, contest_id)
        ensure_contest_running(contest)
        await ensure_can_view_problem_contest(contest, current_user, session)
        contest_registration = await get_contest_registration(session, contest, current_user)
    else:
        if not problem.is_public:
            raise HTTPException(status_code=403, detail="problem.forbidden")

    if submit_form.language not in ["cpp", "py", "text"]:
        raise HTTPException(400, detail="problem.invalid_language")

    submit_data = submit_form.model_dump()
    new_submission = Submission(
        user=current_user,
        problem=problem,
        contest_registration=contest_registration,
        **submit_data,
    )
    session.add(new_submission)
    await session.commit()
    await session.refresh(new_submission)

    payload = {
        "submission_id": new_submission.id,
        "problem_id": problem.id,
        "language": new_submission.language,
        "source": new_submission.source,
    }
    
    await sync_problem_to_redis(request.app.state.redis, problem.id)
    await request.app.state.redis.rpush("submission", json.dumps(payload))

    return new_submission.id


@router.get("/submissions", response_model=Page[SubmissionListOut])
async def get_list_submission(
    session: SessionDep,
    is_best: bool = False,
    contest_id: str | None = None,
    problem_id: str | None = None,
    username: str | None = None,
    current_user: User = Depends(verify_auth),
):
    query = select(Submission).options(
        selectinload(Submission.user),
        selectinload(Submission.problem),
        selectinload(Submission.contest_registration).selectinload(ContestRegistration.contest),
    )

    if contest_id:
        contest = await get_contest_or_404(session, contest_id)
        await ensure_can_view_contest_content(contest, current_user, session)
        reg_ids = select(ContestRegistration.id).where(ContestRegistration.contest_id == contest.id)
        query = query.where(Submission.contest_registration_id.in_(reg_ids))
    if problem_id:
        problem = await get_problem_or_404(session, problem_id)
        query = query.where(Submission.problem_id == problem.id)
    if username:
        user = await get_user_or_404(session, username)
        query = query.where(Submission.user_id == user.id)

    if is_best:
        query = query.order_by(
            case((Submission.status == "AC", 0), else_=1),
            Submission.time.asc(),
            Submission.memory.asc(),
            Submission.id.desc(),
        )
    else:
        query = query.order_by(Submission.id.desc())

    return await apaginate(session, query)


@router.get("/submission/{id}", response_model=SubmissionDetailOut)
async def get_submission(
    request: Request,
    session: SessionDep,
    id: int,
    current_user: User = Depends(verify_auth),
):
    stmt = (
        select(Submission)
        .where(Submission.id == id)
        .options(
            selectinload(Submission.user),
            selectinload(Submission.problem),
            selectinload(Submission.contest_registration).selectinload(ContestRegistration.contest),
        )
    )
    submission = (await session.exec(stmt)).first()
    if not submission:
        raise HTTPException(404, "submission.notfound")
    if current_user.id != submission.user_id:
        raise HTTPException(403, "submission.forbidden")

    live = await request.app.state.redis.get(f"live:{id}")
    if live:
        data = json.loads(live)
        if data.get("status") in ("QW", "C", "P"):
            submission.status = data.get("status", submission.status)
            submission.time = data.get("time", submission.time)
            submission.memory = data.get("memory", submission.memory)
            submission.results = data.get("results", submission.results)

    return submission

