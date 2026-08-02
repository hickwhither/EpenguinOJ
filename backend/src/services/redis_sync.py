import json

from src.database import async_session_maker
from src.models import Problem


# Key: problem:{id}
async def sync_problem_to_redis(redis_client, problem_id: int):
    async with async_session_maker() as session:
        problem = await session.get(Problem, problem_id)

        if not problem:
            await redis_client.delete(f"problem:{problem_id}")
            return

        package = problem.package
        if isinstance(package, str):
            package = json.loads(package)

        problem_payload = {
            "id": problem.id,
            "time_limit": problem.time_limit,
            "memory_limit": problem.memory_limit,
            "input": problem.input,
            "output": problem.output,
            "package": package,
        }

        await redis_client.set(f"problem:{problem.id}", json.dumps(problem_payload))

