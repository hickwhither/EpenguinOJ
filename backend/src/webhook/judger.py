from datetime import datetime, timedelta
from typing import Any
import asyncio
import os
import secrets

from fastapi import APIRouter, Request, HTTPException, Header, Depends, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel
from sqlmodel import select, Session

from src.database import SessionDep, engine
from src.models.submission import Submission, SUBMISSION_STATUS
from src.models.problem import ProblemPublic

# CONFIGURATIONS
router = APIRouter(prefix="/judger", tags=["webhook.judger"])


# SHEMAS
class SubmissionUpdateResult(BaseModel):
    id: int
    status: str
    time_used: float | None = None
    memory_used: float | None = None
    percentage: float | None = None
    error: str | None = None
    results: list[dict[str, Any]] | None = None
    test_cases: list[dict[str, Any]] | None = None


class SubmissionJudge(BaseModel):
    id: int
    language: str
    source: str
    problem: ProblemPublic


# -- DEPENDENCIES / FUNCTIONS --
active_judgers: dict[str, dict[str, Any]] = {}
_waiters: set[asyncio.Event] = set()
_event_loop: asyncio.AbstractEventLoop | None = None


def _now() -> datetime:
    return datetime.now()


def notify_task_available() -> None:
    """Wake websocket judgers when a new submission is queued."""
    if _event_loop and _event_loop.is_running():
        _event_loop.call_soon_threadsafe(_wake_waiters)


def _wake_waiters() -> None:
    for waiter in list(_waiters):
        waiter.set()


def get_judger_infos() -> list[dict[str, Any]]:
    cutoff = _now() - timedelta(seconds=45)
    return [
        {
            "name": name,
            "message": info.get("message"),
            "last_seen": info.get("last_seen"),
            "connected": info.get("connected", False),
            "current_submission_id": info.get("current_submission_id"),
            "status": "online" if info.get("last_seen") and info.get("last_seen") >= cutoff else "offline",
        }
        for name, info in sorted(active_judgers.items())
    ]


def _touch_judger(name: str, message: str | None = None, *, connected: bool | None = None, current_submission_id: int | None = None) -> None:
    info = active_judgers.setdefault(name, {})
    if message is not None:
        info["message"] = message
    if connected is not None:
        info["connected"] = connected
    info["last_seen"] = _now()
    info["current_submission_id"] = current_submission_id


def judge_active(
    request: Request,
    session: SessionDep,
    name: str = Header(..., description="Your name"),
    message: str | None = Header(None, description="whatever you say bro")
) -> str:
    _touch_judger(name, message, connected=False)
    return name


ActiveJudge = Depends(judge_active)


def claim_task(session: Session, judger_name: str) -> Submission | None:
    submission = session.exec(
        select(Submission)
        .where(Submission.status == SUBMISSION_STATUS.QUEUED)
        .order_by(Submission.date_created, Submission.id)
        .with_for_update(skip_locked=True)
    ).first()

    if not submission:
        session.commit()
        return None

    submission.status = SUBMISSION_STATUS.PROCESSING
    submission.judger_name = judger_name
    submission.judged_date = _now()
    session.add(submission)
    session.commit()
    session.refresh(submission)
    _touch_judger(judger_name, connected=True, current_submission_id=submission.id)
    return submission


def save_result(session: Session, payload: SubmissionUpdateResult) -> None:
    submission = session.get(Submission, payload.id)
    if not submission:
        raise HTTPException(404, "Submission not found")

    update_data = payload.model_dump(exclude={"id", "test_cases"}, exclude_unset=True)
    if payload.results is None and payload.test_cases is not None:
        update_data["results"] = payload.test_cases
    submission.sqlmodel_update(update_data)
    session.add(submission)
    session.commit()


# -- ROUTES --
@router.post("/get-task", response_model=SubmissionJudge | None)
def get_task(session: SessionDep, judger_name: str = ActiveJudge):
    return claim_task(session, judger_name)


@router.post("/update-result")
def update_result(payload: SubmissionUpdateResult, session: SessionDep, judger_name: str = ActiveJudge):
    save_result(session, payload)
    _touch_judger(judger_name, connected=False, current_submission_id=None)
    notify_task_available()
    return {"message": "Success"}


@router.websocket("/ws")
async def judger_ws(websocket: WebSocket):
    global _event_loop
    token = websocket.query_params.get("token")
    name = websocket.query_params.get("name") or websocket.headers.get("name")
    message = websocket.query_params.get("message") or websocket.headers.get("message")
    secret_key = os.getenv("SECRET_KEY") or ""

    if not token or not secret_key or not secrets.compare_digest(token, secret_key):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    if not name:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    _event_loop = asyncio.get_running_loop()
    waiter = asyncio.Event()
    _waiters.add(waiter)
    _touch_judger(name, message, connected=True, current_submission_id=None)

    try:
        while True:
            with Session(engine) as session:
                task = claim_task(session, name)
            if task:
                await websocket.send_json({"type": "task", "task": SubmissionJudge.model_validate(task, from_attributes=True).model_dump(mode="json")})
                data = await websocket.receive_json()
                if data.get("type") == "heartbeat":
                    _touch_judger(name, message, connected=True)
                    continue
                if data.get("type") != "result":
                    continue
                with Session(engine) as session:
                    save_result(session, SubmissionUpdateResult(**data.get("result", {})))
                _touch_judger(name, message, connected=True, current_submission_id=None)
                notify_task_available()
            else:
                await websocket.send_json({"type": "idle"})
                try:
                    await asyncio.wait_for(waiter.wait(), timeout=25)
                except asyncio.TimeoutError:
                    await websocket.send_json({"type": "ping"})
                    try:
                        data = await asyncio.wait_for(websocket.receive_json(), timeout=10)
                        if data.get("type") == "heartbeat":
                            _touch_judger(name, message, connected=True)
                    except asyncio.TimeoutError:
                        _touch_judger(name, message, connected=True)
                finally:
                    waiter.clear()
    except WebSocketDisconnect:
        pass
    finally:
        _waiters.discard(waiter)
        _touch_judger(name, message, connected=False, current_submission_id=None)
