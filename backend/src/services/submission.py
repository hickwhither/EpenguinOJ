import json
import asyncio

from src.models.submission import SUBMISSION_STATUS
from src.services.redis_sync import sync_problem_to_redis
from src.database import async_session_maker
from src.models import ContestRegistration, Submission
from src.services.ranking import apply_result_to_registration
from src.services.timing import utcnow


async def rejudge_submissions(session, redis, submissions) -> int:
    """Reset submissions to QUEUED and enqueue them for the judge.

    Returns the number of submissions queued.
    """
    submissions = list(submissions)
    if not submissions:
        return 0

    for problem_id in {sub.problem_id for sub in submissions}:
        await sync_problem_to_redis(redis, problem_id)

    payloads = [
        json.dumps({
            "submission_id": sub.id,
            "problem_id": sub.problem_id,
            "language": sub.language,
            "source": sub.source,
        })
        for sub in submissions
    ]
    await redis.rpush("submission", *payloads)

    for sub in submissions:
        sub.status = SUBMISSION_STATUS.QUEUED
        sub.time = None
        sub.memory = None
        sub.results = None
        sub.error = None
        sub.judger_name = None
        sub.judged_date = None
        session.add(sub)
    await session.commit()

    return len(submissions)


async def apply_result_to_db(session, submission_id: int, data: dict) -> None:
    """Persist a finished judge result onto a submission and its registration."""
    sub = await session.get(Submission, submission_id)
    if not sub:
        return

    sub.status = data.get("status", sub.status)
    sub.time = data.get("time", sub.time)
    sub.memory = data.get("memory", sub.memory)
    sub.results = data.get("results", sub.results)
    sub.error = data.get("error", "")
    sub.judger_name = data.get("judger_name", sub.judger_name)
    sub.judged_date = utcnow()
    session.add(sub)

    if sub.contest_registration_id:
        reg = await session.get(ContestRegistration, sub.contest_registration_id)
        if reg:
            apply_result_to_registration(reg, sub)
            session.add(reg)


async def background_sync_submission(redis_client):
    """Background task: pop finished results from Redis list and persist to DB."""
    while True:
        try:
            result = await redis_client.blpop("results", timeout=1)
            if not result:
                continue
            _, payload = result
            data = json.loads(payload)
            async with async_session_maker() as session:
                await apply_result_to_db(session, data["submission_id"], data)
                await session.commit()
            await redis_client.delete(f"live:{data['submission_id']}")
        except Exception as e:
            print(f"Consumer error: {e}")
            await asyncio.sleep(1)

