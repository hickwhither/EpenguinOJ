from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import select, or_
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate

from src.database import SessionDep
from src.models import User, Contest
from src.models import Problem, ProblemPublic, ProblemView
from src.models import Submission, SubmissionPublic, SubmissionView
from src.dependencies.contest import get_contest_or_404, ensure_contest_running, ensure_can_view_problem_contest
from src.dependencies.user import verify_auth, get_user_or_404


# CONFIGURATION
router = APIRouter(tags=["user.problem"], dependencies=[Depends(verify_auth)])


# SCHEMAS
class SubmissionCreate(BaseModel):
    language: str
    source: str


# FUNCTIONS
def get_problem_or_404(session: SessionDep, id: str) -> Problem:
    problem = session.get(Problem, id)
    if not problem:
        raise HTTPException(404, "problem.notfound")
    return problem


# ROUTERS
@router.get("/problems", response_model=Page[ProblemPublic])
def get_list_problem(
    session: SessionDep,
    search: str | None = None,
    contest_id: str | None = None,
    current_user: User = Depends(verify_auth)
):
    # Contest
    if contest_id:
        contest = get_contest_or_404(session, contest_id)
        ensure_contest_running(contest)
        ensure_can_view_problem_contest(contest, current_user, session)
        query = select(Problem).join(Contest.problems).where(Contest.id == contest_id)
    else:
        query = select(Problem).where(Problem.is_public == True)
    # Filter by name
    if search:
        search_filter = f"%{search.strip()}%"
        query = query.where(Problem.name.ilike(search_filter))
    query = query.order_by(Problem.id.desc())
    return paginate(session, query)


@router.get("/problem", response_model=ProblemView)
def get_problem(
    session: SessionDep,
    problem_id: str,
    contest_id: str | None = None,
    current_user: User = Depends(verify_auth)
):
    problem = get_problem_or_404(session, problem_id)
    if contest_id:
        contest = get_contest_or_404(session, contest_id)
        ensure_contest_running(contest)
        ensure_can_view_problem_contest(contest, current_user, session)
        return problem
    
    if not problem.is_public:
        raise HTTPException(403, "problem.forbidden")
    return problem


@router.post("/submit_code", status_code=201)
def submit_code(
    session: SessionDep,
    submit_form: SubmissionCreate,
    problem_id: str,
    contest_id: str | None = None,
    current_user: User = Depends(verify_auth)
):
    problem = get_problem_or_404(session, problem_id)
    contest = None
    
    if contest_id:
        contest = get_contest_or_404(session, contest_id)
        ensure_contest_running(contest)
        ensure_can_view_problem_contest(contest, current_user, session)
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
        **submit_data
    )
    session.add(new_submission)
    session.commit()
    session.refresh(new_submission)

    return new_submission.id


@router.get('/submissions', response_model=Page[SubmissionPublic])
def get_list_submission(
    session: SessionDep,
    is_best: bool = False,
    contest_id: str | None = None,
    problem_id: str | None = None,
    username: str | None = None,
):
    query = select(Submission)

    if contest_id:
        contest = get_contest_or_404(session, contest_id)
        query = query.where(Submission.contest_id == contest.id)
    if problem_id:
        problem = get_problem_or_404(session, problem_id)
        query = query.where(Submission.problem_id == problem.id)
    if username:
        user = get_user_or_404(session, username)
        query = query.where(Submission.user_id == user.id)

    if is_best:
        query = query.order_by(
            Submission.percentage.desc(),
            Submission.time_used.asc(),
            Submission.memory_used.asc(),
            Submission.id.desc()
        )
    else:
        query = query.order_by(Submission.id.desc())
    
    return paginate(session, query)


@router.get('/submission/{id}', response_model=SubmissionView)
def get_submission(
    session: SessionDep,
    id: int,
    current_user: User = Depends(verify_auth)
):
    submission = session.get(Submission, id)
    if not submission: raise HTTPException(404)
    if current_user.id != submission.user_id: raise HTTPException(403)
    return submission

