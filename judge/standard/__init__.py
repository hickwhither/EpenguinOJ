import json
import os
import shutil

import redis.asyncio as aioredis

from checkers import token
from .runner import (
    compile_cpp,
    run_checker,
    run_generator,
    run_trusted,
    run_validator,
)
from .storage import load_problem, push_final_result, write_live
from submission import Submission


def _new_result_group(st_name, verdict="AC", feedback=None, time_used=0, memory_used=0):
    return {
        "subtask": st_name,
        "verdict": verdict,
        "feedback": feedback,
        "time_used": time_used,
        "memory_used": memory_used,
        "test_cases": [],
    }


def _upsert_group(results, st_name, verdict="AC", feedback=None, time_used=0, memory_used=0):
    group = next((g for g in results if g["subtask"] == st_name), None)
    if group is None:
        group = _new_result_group(st_name, verdict, feedback, time_used, memory_used)
        results.append(group)
    else:
        if group["verdict"] == "AC" and verdict != "AC":
            group["verdict"] = verdict
        if feedback:
            group["feedback"] = feedback
        group["time_used"] = max(group["time_used"], time_used)
        group["memory_used"] = max(group["memory_used"], memory_used)
    return group


def _push_testcase(results, st_name, verdict, time_used, memory_used, feedback=None):
    if verdict == "OK":
        verdict = "AC"
    group = _upsert_group(results, st_name, verdict, time_used=time_used, memory_used=memory_used)
    group["test_cases"].append({
        "verdict": verdict,
        "time_used": time_used,
        "memory_used": memory_used,
        "feedback": feedback,
    })


def _final_verdict(results):
    for group in results:
        if group["verdict"] != "AC":
            return group["verdict"]
    return "AC"


async def _live(redis, submission_id, status, time_used, memory_used, results, judger_name):
    await write_live(redis, submission_id, {
        "status": status,
        "time_used": time_used, "memory_used": memory_used,
        "results": results, "judger_name": judger_name,
    })


async def process_submission(
    payload: dict,
    box_id: int = 0,
    judger_name: str = "judge",
):
    submission_id = payload["submission_id"]
    problem_id = payload["problem_id"]
    language = payload["language"]
    source = payload["source"]

    redis = aioredis.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True
    )

    judge_dir = os.path.join("tmp", f"j_{submission_id}")

    try:
        await _live(redis, submission_id, "C", 0, 0, [], judger_name)

        problem = await load_problem(redis, problem_id)
        if not problem:
            await push_final_result(redis, submission_id, {
                "status": "IE",
                "time_used": 0, "memory_used": 0,
                "results": [_new_result_group(None, "IE", "Problem not found in Redis")],
                "error": "Problem not found", "judger_name": judger_name,
            })
            return

        user = Submission(submission_id, language, source, box_id)
        if not user.is_compiled:
            await push_final_result(redis, submission_id, {
                "status": "CE",
                "time_used": 0, "memory_used": 0,
                "results": [_new_result_group(None, "CE", user.compile_error)],
                "error": "Compilation Error", "judger_name": judger_name,
            })
            return

        os.makedirs(judge_dir, exist_ok=True)

        package = problem.get("package") or {}
        if isinstance(package, str):
            package = json.loads(package)

        answer_src = package.get("answer") or ""
        checker_src = package.get("checker") or ""
        subtasks = package.get("subtasks") or {}
        time_limit = problem.get("time_limit", 1.0)
        memory_limit = problem.get("memory_limit", 32768)

        answer_bin = os.path.join(judge_dir, "ans")
        if not compile_cpp(answer_src, answer_bin, judge_dir):
            await push_final_result(redis, submission_id, {
                "status": "IE",
                "time_used": 0, "memory_used": 0,
                "results": [_new_result_group(None, "IE", "Failed to compile official answer")],
                "error": "Answer compile failed", "judger_name": judger_name,
            })
            return

        checker_bin = None
        if checker_src.strip():
            checker_bin = os.path.join(judge_dir, "checker")
            if not compile_cpp(checker_src, checker_bin, judge_dir):
                await push_final_result(redis, submission_id, {
                    "status": "IE",
                    "time_used": 0, "memory_used": 0,
                    "results": [_new_result_group(None, "IE", "Failed to compile checker")],
                    "error": "Checker compile failed", "judger_name": judger_name,
                })
                return

        results = []
        time_used = 0.0
        memory_used = 0.0

        input_path = os.path.join(user.work_dir, "input")
        output_path = os.path.join(user.work_dir, "output")
        expected_path = os.path.join(judge_dir, "expected")

        await _live(redis, submission_id, "P", 0, 0, [], judger_name)

        for st_name, cfg in subtasks.items():
            validator_src = cfg.get("validator") or ""
            generators = cfg.get("generators", [])

            validator_bin = None
            if validator_src and validator_src.strip():
                validator_bin = os.path.join(judge_dir, f"valid_{st_name}")
                if not compile_cpp(validator_src, validator_bin, judge_dir):
                    _upsert_group(results, st_name, "IE", "Validator compile failed")
                    await _live(redis, submission_id, "P", time_used, memory_used, results, judger_name)
                    continue

            gen_bins = []
            gen_ok = True
            for i, gen in enumerate(generators):
                gen_src = gen.get("code") or ""
                gen_bin = os.path.join(judge_dir, f"gen_{st_name}_{i}")
                if not compile_cpp(gen_src, gen_bin, judge_dir):
                    _upsert_group(results, st_name, "IE", "Generator compile failed")
                    gen_ok = False
                    break
                gen_bins.append(gen_bin)
            if not gen_ok:
                await _live(redis, submission_id, "P", time_used, memory_used, results, judger_name)
                continue

            group_passed = True
            for gen_bin in gen_bins:
                args = gen.get("args", [])
                for arg in args:
                    gen_res = run_generator(gen_bin, str(arg), input_path, 30.0)
                    if gen_res["status"] != "OK":
                        _upsert_group(results, st_name, "IE", f"Generator: {gen_res.get('error', '')}")
                        group_passed = False
                        break

                    if validator_bin:
                        valid_res = run_validator(validator_bin, input_path, 10.0)
                        if valid_res["status"] != "OK":
                            _upsert_group(results, st_name, "IE", f"Validator: {valid_res.get('error', '')}")
                            group_passed = False
                            break

                    ans_res = run_trusted(answer_bin, input_path, expected_path, time_limit)
                    if ans_res["status"] != "OK":
                        _upsert_group(results, st_name, "IE", f"Answer: {ans_res.get('error', '')}")
                        group_passed = False
                        break

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

                    _push_testcase(results, st_name, verdict, res.get("time_used", 0), res.get("memory_used", 0), feedback)

                    time_used = max(time_used, res.get("time_used", 0))
                    memory_used = max(memory_used, res.get("memory_used", 0))

                    await _live(redis, submission_id, "P", time_used, memory_used, results, judger_name)

                    if verdict != "AC":
                        group_passed = False
                        break

                if not group_passed:
                    break

        await push_final_result(redis, submission_id, {
            "status": _final_verdict(results),
            "time_used": time_used, "memory_used": memory_used,
            "results": results, "error": None, "judger_name": judger_name,
        })

    except Exception as e:
        await push_final_result(redis, submission_id, {
            "status": "IE",
            "time_used": 0, "memory_used": 0,
            "results": [_new_result_group(None, "IE", f"Judge error: {e}")],
            "error": str(e), "judger_name": judger_name,
        })
    finally:
        if 'user' in locals():
            user.cleanup()
        shutil.rmtree(judge_dir, ignore_errors=True)
        await redis.close()
