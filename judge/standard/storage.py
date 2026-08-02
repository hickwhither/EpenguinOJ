import json


async def write_live(redis, submission_id: str, data: dict) -> None:
    await redis.set(f"live:{submission_id}", json.dumps(data), ex=600)


async def push_final_result(redis, submission_id: str, payload: dict) -> None:
    payload["submission_id"] = submission_id
    data_str = json.dumps(payload)

    await redis.rpush("results", data_str)
    await write_live(redis, submission_id, payload)


async def load_problem(redis, problem_id: str) -> dict | None:
    problem_raw = await redis.get(f"problem:{problem_id}")
    if not problem_raw:
        return None

    return json.loads(problem_raw)
