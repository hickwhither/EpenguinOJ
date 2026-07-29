import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import apaginate
from pydantic import BaseModel
from sqlmodel import or_, select
from starlette.responses import StreamingResponse

from src.database import SessionDep
from src.dependencies.contest import (
    ensure_can_view_problem_contest,
    ensure_contest_running,
    get_contest_or_404,
)
from src.dependencies.user import get_user_or_404, verify_auth
from src.models import (
    Contest,
    Problem,
    ProblemPublic,
    ProblemView,
    Submission,
    SUBMISSION_STATUS,
    SubmissionPublic,
    SubmissionView,
    User,
)

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
    contest_id: str | None = None,
    current_user: User = Depends(verify_auth),
):
    # Contest
    if contest_id:
        contest = await get_contest_or_404(session, contest_id)
        ensure_contest_running(contest)
        await ensure_can_view_problem_contest(contest, current_user, session)
        query = select(Problem).where(Problem.contests.any(Contest.id == contest_id))
    else:
        query = select(Problem).where(Problem.is_public == True)

    # Filter by name
    if search:
        search_filter = f"%{search.strip()}%"
        query = query.where(Problem.name.ilike(search_filter))
        
    query = query.order_by(Problem.id.desc())
    return await apaginate(session, query)


@router.get("/problem", response_model=ProblemView)
async def get_problem(
    session: SessionDep,
    problem_id: str,
    contest_id: str | None = None,
    current_user: User = Depends(verify_auth),
):
    problem = await get_problem_or_404(session, problem_id)
    if contest_id:
        contest = await get_contest_or_404(session, contest_id)
        ensure_contest_running(contest)
        await ensure_can_view_problem_contest(contest, current_user, session)
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

    if contest_id:
        contest = await get_contest_or_404(session, contest_id)
        ensure_contest_running(contest)
        await ensure_can_view_problem_contest(contest, current_user, session)
    else:
        if not problem.is_public:
            raise HTTPException(status_code=403, detail="problem.forbidden")

    if submit_form.language not in ["cpp", "py", "text"]:
        raise HTTPException(400, detail="problem.invalid_language")

    submit_data = submit_form.model_dump()
    new_submission = Submission(
        user=current_user,
        problem=problem,
        contest=contest,
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

    await request.app.state.redis.rpush("submission", json.dumps(payload))

    return new_submission.id


@router.get("/submissions", response_model=Page[SubmissionPublic])
async def get_list_submission(
    session: SessionDep,
    is_best: bool = False,
    contest_id: str | None = None,
    problem_id: str | None = None,
    username: str | None = None,
):
    query = select(Submission)

    if contest_id:
        contest = await get_contest_or_404(session, contest_id)
        query = query.where(Submission.contest_id == contest.id)
    if problem_id:
        problem = await get_problem_or_404(session, problem_id)
        query = query.where(Submission.problem_id == problem.id)
    if username:
        user = await get_user_or_404(session, username)
        query = query.where(Submission.user_id == user.id)

    if is_best:
        query = query.order_by(
            Submission.score.desc(),
            Submission.time_used.asc(),
            Submission.memory_used.asc(),
            Submission.id.desc(),
        )
    else:
        query = query.order_by(Submission.id.desc())

    return await apaginate(session, query)


@router.get("/submission/{id}", response_model=SubmissionView)
async def get_submission(
    request: Request,
    session: SessionDep,
    id: int,
    current_user: User = Depends(verify_auth),
):
    submission = await session.get(Submission, id)
    if not submission:
        raise HTTPException(404, "submission.notfound")
    if current_user.id != submission.user_id:
        raise HTTPException(403, "submission.forbidden")

    live = await request.app.state.redis.get(f"live:{id}")
    if live:
        data = json.loads(live)
        if data.get("status") != SUBMISSION_STATUS.DONE:
            submission.status = data.get("status", submission.status)
            submission.score = data.get("score", submission.score)
            submission.max_score = data.get("max_score", submission.max_score)
            submission.time_used = data.get("time_used", submission.time_used)
            submission.memory_used = data.get("memory_used", submission.memory_used)

    return submission


@router.get("/submission/{id}/stream")
async def stream_submission(
    request: Request,
    session: SessionDep,
    id: int,
    current_user: User = Depends(verify_auth),
):
    submission = await session.get(Submission, id)
    if not submission:
        raise HTTPException(404, "submission.notfound")
    if current_user.id != submission.user_id:
        raise HTTPException(403, "submission.forbidden")

    async def event_generator():
        last_data = None
        while True:
            live = await request.app.state.redis.get(f"live:{id}")
            if live:
                data = json.loads(live)
                if data != last_data:
                    last_data = data
                    yield f"data: {json.dumps(data)}\n\n"
                    if data.get("status") == SUBMISSION_STATUS.DONE:
                        break
            else:
                if last_data is None:
                    yield f"data: {json.dumps({'status': submission.status, 'score': submission.score, 'max_score': submission.max_score})}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

