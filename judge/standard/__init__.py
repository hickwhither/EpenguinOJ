import json
import os
import shutil

import redis.asyncio as Redis

from checkers import token
from .runner import (
    compile_cpp,
    run_checker,
    run_generator,
    run_trusted,
    run_validator,
)
from submission import Submission


async def redis_live(redis_client: Redis, submission_id, payload):
    await redis_client.set(f"live:{submission_id}", json.dumps(payload), ex=600)


async def redis_push_final_result(redis_client: Redis, submission_id: str, payload: dict) -> None:
    payload["submission_id"] = submission_id
    data_str = json.dumps(payload)

    await redis_live(redis_client, submission_id, payload)
    await redis_client.rpush("results", data_str)


async def redis_load_problem(redis_client: Redis, problem_id: str) -> dict | None:
    problem_raw = await redis_client.get(f"problem:{problem_id}")
    if not problem_raw:
        return None

    return json.loads(problem_raw)


async def process_submission(
    redis_client: Redis,
    payload: dict,
    box_id: int = 0,
    judger_name: str = "judge",
):
    submission_id = payload["submission_id"]
    problem_id = payload["problem_id"]
    language = payload["language"]
    source = payload["source"]

    judge_dir = os.path.join("tmp", f"j_{submission_id}")

    try:
        await redis_live(redis_client, submission_id, {
            "status": "C",
            "judger_name": judger_name,
        })

        problem = await redis_load_problem(redis_client, problem_id)
        if not problem:
            await redis_push_final_result(redis_client, submission_id, {
                "status": "IE",
                "error": "Problem not found on Redis",
                "judger_name": judger_name,
            })
            return

        user = Submission(submission_id, language, source, box_id)
        if not user.is_compiled:
            await redis_push_final_result(redis_client, submission_id, {
                "status": "CE",
                "error": user.compile_error,
                "judger_name": judger_name,
            })
            return

        os.makedirs(judge_dir, exist_ok=True)

        package = problem.get("package") or {}
        if isinstance(package, str):
            package = json.loads(package)

        answer_src = package.get("answer") or ""
        validator_src = package.get("validator") or ""
        checker_src = package.get("checker") or ""
        generators = package.get("generators") or []
        time_limit = problem.get("time_limit", 1.0)
        memory_limit = problem.get("memory_limit", 32768)

        answer_bin = os.path.join(judge_dir, "ans")
        if not compile_cpp(answer_src, answer_bin, judge_dir):
            await redis_push_final_result(redis_client, submission_id, {
                "status": "IE",
                "error": "Answer compile failed",
                "judger_name": judger_name,
            })
            return

        validator_bin = os.path.join(judge_dir, "validator")
        if validator_src.strip():
            if not compile_cpp(validator_src, validator_bin, judge_dir):
                await redis_push_final_result(redis_client, submission_id, {
                    "status": "IE",
                    "error": "Validator compile failed",
                    "judger_name": judger_name,
                })
                return

        checker_bin = None
        if checker_src.strip():
            checker_bin = os.path.join(judge_dir, "checker")
            if not compile_cpp(checker_src, checker_bin, judge_dir):
                await redis_push_final_result(redis_client, submission_id, {
                    "status": "IE",
                    "error": "Checker compile failed",
                    "judger_name": judger_name,
                })
                return

        results = []
        time = 0.0
        memory = 0.0

        input_path = os.path.join(user.work_dir, "input")
        output_path = os.path.join(user.work_dir, "output")
        expected_path = os.path.join(judge_dir, "expected")

        await redis_live(redis_client, submission_id, {
            "status": "P",
            "judger_name": judger_name,
        })

        for cfg in generators:
            name = cfg.get("name") or "default"
            gen_src = cfg.get("code") or ""
            gen_bin = os.path.join(judge_dir, f"gen_{name}")
            if not compile_cpp(gen_src, gen_bin, judge_dir):
                results.append({
                    "group": name,
                    "status": "IE",
                    "error": "Generator compile failed",
                })
                await redis_push_final_result(redis_client, submission_id, {
                    "status": "IE",
                    "error": "Generator compile failed",
                    "judger_name": judger_name,
                })
                return
            args = cfg.get("args", [])
            for arg in args:
                gen_res = run_generator(gen_bin, str(arg), input_path, 30.0)
                if gen_res["status"] != "OK":
                    results.append({
                        "group": name,
                        "status": "IE",
                        "error": f"Generator {name}: {gen_res.get('error', '')}",
                    })
                    await redis_push_final_result(redis_client, submission_id, {
                        "status": "IE",
                        "results": results,
                        "error": f"Generator {name}: {gen_res.get('error', '')}",
                        "judger_name": judger_name,
                    })
                    return

                if validator_bin:
                    valid_res = run_validator(validator_bin, input_path, 10.0)
                    if valid_res["status"] != "OK":
                        results.append({
                            "group": name,
                            "status": "IE",
                            "error": f"Validator: {valid_res.get('error', '')}",
                        })
                        await redis_push_final_result(redis_client, submission_id, {
                            "status": "IE",
                            "results": results,
                            "error": f"Validator: {valid_res.get('error', '')}",
                            "judger_name": judger_name,
                        })
                        return

                ans_res = run_trusted(answer_bin, input_path, expected_path, time_limit)
                if ans_res["status"] != "OK":
                    results.append({
                        "group": name,
                        "status": "IE",
                        "error": f"Answer: {ans_res.get('error', '')}",
                    })
                    await redis_push_final_result(redis_client, submission_id, {
                        "status": "IE",
                        "results": results,
                        "error": f"Answer: {ans_res.get('error', '')}",
                        "judger_name": judger_name,
                    })
                    return

                res = user.run(time_limit=time_limit, memory_limit=memory_limit)

                verdict = res.get("status", "IE")
                feedback = None
                if verdict == "OK":
                    if checker_bin:
                        chk = run_checker(checker_bin, input_path, output_path, expected_path, 10.0)
                        verdict = "AC" if chk["status"] == "OK" else chk["status"]
                        feedback = chk.get("error")
                    else:
                        fb = token.check(output_path, expected_path)
                        verdict = "WA" if fb else "AC"
                        feedback = fb

                results.append({
                    "group": name,
                    "status": verdict,
                    "time": res.get("time", 0),
                    "memory": res.get("memory", 0),
                    "feedback": feedback,
                })

                time = max(time, res.get("time", 0))
                memory = max(memory, res.get("memory", 0))
                
                await redis_live(redis_client, submission_id, {
                    "status": "P",
                    "results": results,
                    "judger_name": judger_name,
                })

                if verdict != "AC":
                    await redis_push_final_result(redis_client, submission_id, {
                        "status": verdict,
                        "time": time, "memory": memory,
                        "results": results,
                        "error": feedback,
                        "judger_name": judger_name,
                    })
                    return

        await redis_push_final_result(redis_client, submission_id, {
            "status": "AC",
            "time": time, "memory": memory,
            "results": results,
            "judger_name": judger_name,
        })

    except Exception as e:
        await redis_push_final_result(redis_client, submission_id, {
            "status": "IE",
            "error": str(e),
            "judger_name": judger_name,
        })
    finally:
        if 'user' in locals():
            user.cleanup()
        shutil.rmtree(judge_dir, ignore_errors=True)
        await redis_client.close()
