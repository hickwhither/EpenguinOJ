from datetime import datetime

from src.utils import utcnow
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from sqlmodel import select
from pydantic import BaseModel
from pathlib import Path

from src.database import SessionDep
from src.models import ContestRegistration, Problem, Submission
from src.services.ranking import apply_result_to_registration

# CONFIGURATIONS
router = APIRouter(prefix="/judger", tags=["webhook.judger"])

BASE_PROBLEMS_DIR = Path("tmp/problems").resolve()


class StatusUpdate(BaseModel):
    status: str
    score: float | None = None
    max_score: float | None = None


class TestCaseResult(BaseModel):
    verdict: str
    time_used: float = 0.0
    memory_used: float = 0.0
    feedback: str | None = None


class SubtaskResult(BaseModel):
    subtask: str | int | None = None
    verdict: str | None = None
    time_used: float = 0.0
    memory_used: float = 0.0
    feedback: str | None = None
    test_cases: list[TestCaseResult] = []


class JudgeResult(BaseModel):
    status: str
    score: float = 0.0
    max_score: float = 0.0
    time_used: float = 0.0
    memory_used: float = 0.0
    results: list[SubtaskResult] = []
    error: str | None = None
    judger_name: str = ""


@router.patch('/{submission_id}/status')
async def update_status(session: SessionDep, submission_id: int, body: StatusUpdate):
    submission = await session.get(Submission, submission_id)
    if not submission:
        raise HTTPException(404, "submission.notfound")
    submission.status = body.status
    if body.score is not None:
        submission.score = body.score
    if body.max_score is not None:
        submission.max_score = body.max_score
    session.add(submission)
    await session.commit()
    return {"ok": True}


@router.post('/{submission_id}/result')
async def report_result(session: SessionDep, submission_id: int, body: JudgeResult):
    submission = await session.get(Submission, submission_id)
    if not submission:
        raise HTTPException(404, "submission.notfound")

    submission.status = body.status
    submission.score = body.score
    submission.max_score = body.max_score
    submission.time_used = body.time_used
    submission.memory_used = body.memory_used
    submission.results = [r.model_dump() for r in body.results]
    submission.error = body.error
    submission.judger_name = body.judger_name
    submission.judged_date = utcnow()
    session.add(submission)

    if submission.contest_id:
        stmt = select(ContestRegistration).where(
            ContestRegistration.contest_id == submission.contest_id,
            ContestRegistration.user_id == submission.user_id,
        )
        reg = (await session.scalars(stmt)).first()
        if reg:
            apply_result_to_registration(reg, submission)
            session.add(reg)

    await session.commit()
    return {"ok": True}


@router.get('/{id}')
@router.get('/{id}/{path:path}')
async def serve_file(session: SessionDep, id: int, path: str | None = None):
    if not path:
        problem = await session.get(Problem, id)
        if not problem:
            raise HTTPException(status_code=404, detail="Problem not found")
        return problem.subtasks

    problem_dir = (BASE_PROBLEMS_DIR / str(id)).resolve()
    file_path = (problem_dir / path).resolve()
    if not str(file_path).startswith(str(problem_dir)) or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found or access denied")
    return FileResponse(path=file_path)
