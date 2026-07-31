from fastapi import HTTPException, Request
from sqlmodel import select

from src.utils import utcnow

from src.database import SessionDep
from src.models import User
from src.models import Contest, ContestRegistration


async def get_contest_or_404(session: SessionDep, id: str) -> Contest:
    contest = await session.get(Contest, id)
    if not contest:
        raise HTTPException(404, "contest.notfound")
    return contest


def is_contest_running(contest: Contest) -> None:
    now = utcnow()
    if now < contest.start_time:
        return False
    if now > contest.end_time:
        return False
    return True


def ensure_contest_running(contest: Contest) -> None:
    now = utcnow()
    if now < contest.start_time:
        raise HTTPException(403, "contest.upcoming")
    if now > contest.end_time:
        raise HTTPException(403, "contest.ended")


def ensure_registration_running(contest: Contest) -> None:
    now = utcnow()
    if contest.registration_start and now < contest.registration_start:
        raise HTTPException(403, "contest.registration_upcoming")
    if contest.registration_end and now > contest.registration_end:
        raise HTTPException(403, "contest.registration_ended")
    if now > contest.end_time:
        raise HTTPException(403, "contest.ended")


async def is_contest_participant(session: SessionDep, contest: Contest, user: User) -> bool:
    return bool(await session.get(ContestRegistration, (contest.id, user.id)))


async def ensure_can_view_problem_contest(contest: Contest, user: User, session: SessionDep) -> None:
    if await is_contest_participant(session, contest, user):
        return
    raise HTTPException(403, "contest.not_registered")