from fastapi import HTTPException
from sqlmodel import select

from src.database import SessionDep
from src.models import Contest, ContestRegistration, User
from src.services.timing import utcnow


async def get_contest_or_404(session: SessionDep, id: str) -> Contest:
    contest = await session.get(Contest, id)
    if not contest:
        raise HTTPException(404, "contest.notfound")
    return contest


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


async def get_contest_registration(session: SessionDep, contest: Contest, user: User) -> ContestRegistration | None:
    stmt = select(ContestRegistration).where(
        ContestRegistration.contest_id == contest.id,
        ContestRegistration.user_id == user.id,
    )
    return (await session.scalars(stmt)).first()


async def is_contest_participant(session: SessionDep, contest: Contest, user: User) -> bool:
    return bool(await get_contest_registration(session, contest, user))


async def ensure_can_view_problem_contest(contest: Contest, user: User, session: SessionDep) -> None:
    if await is_contest_participant(session, contest, user):
        return
    raise HTTPException(403, "contest.not_registered")


async def ensure_can_view_contest_content(contest: Contest, user: User, session: SessionDep) -> None:
    """Gate for viewing contest content (problems, submissions, ranking).

    Hidden before the contest starts, registered-only while it is running,
    and public after it ends.
    """
    now = utcnow()
    if now < contest.start_time:
        raise HTTPException(403, "contest.upcoming")
    if now <= contest.end_time and not await is_contest_participant(session, contest, user):
        raise HTTPException(403, "contest.not_registered")

