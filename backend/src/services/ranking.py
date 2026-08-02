from sqlalchemy import select

from src.models import Contest, ContestRegistration, Submission


def penalty_minutes(reg: ContestRegistration, contest: Contest) -> float:
    """Penalty in minutes relative to the contest start (last AC epoch)."""
    if not contest.start_time:
        return 0.0
    return (reg.penalty - contest.start_time) / 60.0


def apply_result_to_registration(reg: ContestRegistration, sub: Submission) -> None:
    """Incrementally update a registration's ranking fields with a finished submission.

    A problem is solved (worth 1 point) once any submission for it is AC.
    Penalty is the epoch of the latest first-AC among the solved problems.
    """
    if sub.status != "AC":
        return

    key = str(sub.problem_id)
    if reg.problem_scores.get(key, 0) != 1:
        problem_scores = dict(reg.problem_scores or {})
        problem_scores[key] = 1
        reg.problem_scores = problem_scores
        reg.penalty = max(reg.penalty, sub.date_created)
        reg.total_score = sum(problem_scores.values())


async def recompute_registration(session, contest_id: int, user_id: int) -> ContestRegistration | None:
    """Recompute a registration's ranking fields from its finished submissions."""
    stmt = select(ContestRegistration).where(
        ContestRegistration.contest_id == contest_id,
        ContestRegistration.user_id == user_id,
    )
    reg = (await session.scalars(stmt)).first()
    if reg is None:
        return None

    subs_stmt = (
        select(Submission)
        .where(
            Submission.contest_registration_id == reg.id,
            Submission.status == "AC",
        )
        .order_by(Submission.date_created.asc(), Submission.id.asc())
    )
    subs = (await session.scalars(subs_stmt)).all()

    problem_scores: dict[str, float] = {}
    penalty = 0
    for sub in subs:
        key = str(sub.problem_id)
        if problem_scores.get(key, 0) != 1:
            problem_scores[key] = 1
            penalty = max(penalty, sub.date_created)

    reg.problem_scores = problem_scores
    reg.total_score = sum(problem_scores.values())
    reg.penalty = penalty
    session.add(reg)
    return reg


async def backfill_all(session) -> int:
    """Recompute ranking fields for every contest registration."""
    regs = (await session.scalars(select(ContestRegistration))).all()
    for reg in regs:
        await recompute_registration(session, reg.contest_id, reg.user_id)
    await session.commit()
    return len(regs)
