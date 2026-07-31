from sqlalchemy.orm import selectinload
from sqlmodel import select

from src.models import Contest, ContestRegistration, Submission

PENALTY_PER_SUBMISSION = 5.0


def apply_result_to_registration(reg: ContestRegistration, sub: Submission) -> None:
    """Incrementally update a registration's ranking fields with a finished submission.

    A submission raises the personal-best total only when it beats the current
    best score of its problem (total == sum of per-problem bests). Submissions
    that don't improve the total add a 5-minute penalty.
    """
    key = str(sub.problem_id)
    old = float(reg.problem_scores.get(key, 0.0))
    if sub.score > old:
        reg.problem_scores[key] = sub.score
        reg.total_score = sum(reg.problem_scores.values())
        reg.last_improve_time = sub.date_created
    else:
        reg.penalty += PENALTY_PER_SUBMISSION


def penalty_minutes(reg: ContestRegistration, contest: Contest) -> float:
    """Full penalty: 5-min increments plus the last-improve time term."""
    total = float(reg.penalty)
    if reg.last_improve_time and contest.start_time:
        total += (reg.last_improve_time - contest.start_time) / 60.0
    return total


async def recompute_registration(session, contest_id: int, user_id: int) -> ContestRegistration | None:
    """Recompute a registration's ranking fields from its finished submissions.

    Simulates the submissions chronologically (by date_created) to rebuild
    per-problem best scores, total score, 5-min penalty count and the last time
    a new high total was set.
    """
    reg = await session.get(ContestRegistration, (contest_id, user_id))
    if reg is None:
        return None

    stmt = (
        select(Submission)
        .where(
            Submission.contest_id == contest_id,
            Submission.user_id == user_id,
            Submission.status == "D",
        )
        .order_by(Submission.date_created.asc(), Submission.id.asc())
    )
    subs = (await session.scalars(stmt)).all()

    problem_scores: dict[str, float] = {}
    best_total = 0.0
    last_improve_time = None
    non_improve = 0.0

    for sub in subs:
        key = str(sub.problem_id)
        if sub.score > problem_scores.get(key, 0.0):
            problem_scores[key] = sub.score
            best_total = sum(problem_scores.values())
            last_improve_time = sub.date_created
        else:
            non_improve += PENALTY_PER_SUBMISSION

    reg.problem_scores = problem_scores
    reg.total_score = sum(problem_scores.values())
    reg.penalty = non_improve
    reg.last_improve_time = last_improve_time
    session.add(reg)
    return reg


async def backfill_all(session) -> int:
    """Recompute ranking fields for every contest registration."""
    regs = (await session.scalars(select(ContestRegistration))).all()
    for reg in regs:
        await recompute_registration(session, reg.contest_id, reg.user_id)
    await session.commit()
    return len(regs)
