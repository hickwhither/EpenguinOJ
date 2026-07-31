import json
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.database import async_session_maker
from src.models import Submission, Hack, Problem, Subtask

# Key: hack:{id}
async def sync_hack_to_redis(redis_client, hack_id: int):
    async with async_session_maker() as session:
        hack = await session.get(Hack, hack_id)

        if not hack:
            await redis_client.delete(f"hack:{hack_id}")
            return None

        hack_payload = {"id": hack.id, "language": hack.language, "source": hack.source}

        await redis_client.set(f"hack:{hack.id}", json.dumps(hack_payload))


# Key: subtask:{id}
async def sync_subtask_to_redis(redis_client, subtask_id: int):
    async with async_session_maker() as session:
        statement = (
            select(Subtask)
            .where(Subtask.id == subtask_id)
            .options(selectinload(Subtask.hacks))
        )
        result = await session.scalars(statement)
        subtask = result.first()

        if not subtask:
            await redis_client.delete(f"subtask:{subtask_id}")
            return None

        hack_ids = []
        for hack in subtask.hacks:
            await sync_hack_to_redis(redis_client, hack.id)
            hack_ids.append(hack.id)

        seeds = subtask.seeds
        if isinstance(seeds, str):
            seeds = json.loads(seeds)

        subtask_payload = {
            "id": subtask.id,
            "points": subtask.points,
            "generator": subtask.generator,
            "validator": subtask.validator,
            "seeds": seeds,
            "hacks": hack_ids,
        }

        await redis_client.set(f"subtask:{subtask.id}", json.dumps(subtask_payload))


# Key: problem:{id}
async def sync_problem_to_redis(redis_client, problem_id: int):
    async with async_session_maker() as session:
        statement = (
            select(Problem)
            .where(Problem.id == problem_id)
            .options(selectinload(Problem.subtasks).selectinload(Subtask.hacks))
        )
        result = await session.scalars(statement)
        problem = result.first()

        if not problem:
            await redis_client.delete(f"problem:{problem_id}")
            return

        subtask_ids = []
        for st in problem.subtasks:
            await sync_subtask_to_redis(redis_client, st.id)
            subtask_ids.append(st.id)

        problem_payload = {
            "id": problem.id,
            "time_limit": problem.time_limit,
            "memory_limit": problem.memory_limit,
            "input": problem.input,
            "output": problem.output,
            "answer": problem.answer,
            "subtasks": subtask_ids,
        }

        await redis_client.set(f"problem:{problem.id}", json.dumps(problem_payload))

