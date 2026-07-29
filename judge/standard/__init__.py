import json
import os
import shutil
import subprocess

from redis.asyncio import aioredis

from checkers import token
from submission import Submission


def _compile_cpp(source: str, output_path: str, work_dir: str) -> bool:
    src_path = os.path.join(work_dir, "_src.cpp")
    with open(src_path, "w", encoding="utf-8") as f:
        f.write(source)
    cmd = [
        "/usr/bin/g++", "-std=c++14", "-Wall", "-DONLINE_JUDGE", "-O2",
        "-lm", "-fmax-errors=5", "-march=native", "-s",
        src_path, "-o", output_path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return proc.returncode == 0 and os.path.exists(output_path)


def _run_trusted(exec_path: str, input_path: str, output_path: str, time_limit: float) -> dict:
    try:
        with open(input_path, "r") as inf, open(output_path, "w") as outf:
            subprocess.run([exec_path], stdin=inf, stdout=outf, timeout=time_limit + 5)
        return {"status": "OK"}
    except subprocess.TimeoutExpired:
        return {"status": "TLE"}
    except Exception as e:
        return {"status": "IE", "error": str(e)}


def _run_generator(exec_path: str, seed: int, output_path: str, time_limit: float) -> dict:
    try:
        with open(output_path, "w") as outf:
            subprocess.run([exec_path, str(seed)], stdout=outf, timeout=time_limit)
        return {"status": "OK"}
    except subprocess.TimeoutExpired:
        return {"status": "TLE"}
    except Exception as e:
        return {"status": "IE", "error": str(e)}


async def _write_live(redis, submission_id: str, data: dict) -> None:
    await redis.set(f"live:{submission_id}", json.dumps(data), ex=600)


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

    try:
        await _write_live(redis, submission_id, {
            "status": "C", "score": 0, "max_score": 0,
            "time_used": 0, "memory_used": 0, "results": [],
            "judger_name": judger_name,
        })

        # ---- Load problem data from Redis ----
        problem_raw = await redis.get(f"problem:{problem_id}")
        if not problem_raw:
            await _write_live(redis, submission_id, {
                "status": "D", "score": 0, "max_score": 0,
                "time_used": 0, "memory_used": 0,
                "results": [{"verdict": "IE", "feedback": "Problem not found in Redis"}],
                "error": "Problem not found", "judger_name": judger_name,
            })
            await redis.rpush("results", json.dumps({
                "submission_id": submission_id,
                "status": "D", "score": 0, "max_score": 0,
                "time_used": 0, "memory_used": 0,
                "results": [{"verdict": "IE", "feedback": "Problem not found in Redis"}],
                "error": "Problem not found", "judger_name": judger_name,
            }))
            return

        problem = json.loads(problem_raw)

        subtasks = []
        for st_id in problem.get("subtasks", []):
            st_raw = await redis.get(f"subtask:{st_id}")
            if st_raw:
                subtasks.append(json.loads(st_raw))

        # ---- Compile user submission ----
        user = Submission(submission_id, language, source, box_id)
        if not user.is_compiled:
            await redis.rpush("results", json.dumps({
                "submission_id": submission_id,
                "status": "D", "score": 0, "max_score": 0,
                "time_used": 0, "memory_used": 0,
                "results": [{"verdict": "CE", "feedback": user.compile_error}],
                "error": "Compilation Error", "judger_name": judger_name,
            }))
            user.cleanup()
            return

        # ---- Compile answer (C++ default) ----
        judge_dir = os.path.join("tmp", f"j_{submission_id}")
        os.makedirs(judge_dir, exist_ok=True)

        answer_src = problem.get("answer", "")
        answer_bin = os.path.join(judge_dir, "ans")
        if not _compile_cpp(answer_src, answer_bin, judge_dir):
            await redis.rpush("results", json.dumps({
                "submission_id": submission_id, "judger_name": judger_name,
                "status": "D", "score": 0, "max_score": 0,
                "time_used": 0, "memory_used": 0,
                "results": [{"verdict": "IE", "feedback": "Failed to compile official answer"}],
                "error": "Answer compile failed",
            }))
            user.cleanup()
            shutil.rmtree(judge_dir, ignore_errors=True)
            return

        # ---- Judge loop ----
        results = []
        total_score = 0
        max_score = 0
        time_used = 0.0
        memory_used = 0.0

        input_path = os.path.join(user.work_dir, "input")
        output_path = os.path.join(user.work_dir, "output")
        expected_path = os.path.join(judge_dir, "expected")

        await _write_live(redis, submission_id, {
            "status": "P", "score": 0, "max_score": 0,
            "time_used": 0, "memory_used": 0, "results": [],
            "judger_name": judger_name,
        })

        for subtask in subtasks:
            st_points = subtask.get("points", 0)
            max_score += st_points
            st_name = subtask.get("name", f"subtask_{subtask.get('id', '?')}")

            gen_src = subtask.get("generator", "")
            gen_bin = os.path.join(judge_dir, f"gen_{subtask.get('id', '?')}")
            if not _compile_cpp(gen_src, gen_bin, judge_dir):
                results.append({"subtask": st_name, "verdict": "IE", "feedback": "Generator compile failed", "time_used": 0, "memory_used": 0})
                await _write_live(redis, submission_id, {
                    "status": "P", "score": total_score, "max_score": max_score,
                    "time_used": time_used, "memory_used": memory_used,
                    "results": results, "judger_name": judger_name,
                })
                continue

            group_passed = True
            seeds = subtask.get("seeds", [])

            for seed in seeds:
                gen_res = _run_generator(gen_bin, seed, input_path, 30.0)
                if gen_res["status"] != "OK":
                    results.append({"subtask": st_name, "verdict": "IE", "feedback": f"Generator: {gen_res.get('error', '')}", "time_used": 0, "memory_used": 0})
                    group_passed = False
                    break

                ans_res = _run_trusted(answer_bin, input_path, expected_path, problem.get("time_limit", 1.0))
                if ans_res["status"] != "OK":
                    results.append({"subtask": st_name, "verdict": "IE", "feedback": f"Answer: {ans_res.get('error', '')}", "time_used": 0, "memory_used": 0})
                    group_passed = False
                    break

                res = user.run(
                    time_limit=problem.get("time_limit", 1.0),
                    memory_limit=problem.get("memory_limit", 32768),
                )

                verdict = res.get("status", "IE")
                feedback = None
                if verdict == "OK":
                    fb = token.check(output_path, expected_path)
                    verdict = "WA" if fb else "AC"
                    feedback = fb

                tc_res = {
                    "subtask": st_name,
                    "time_used": res.get("time_used", 0),
                    "memory_used": res.get("memory_used", 0),
                    "verdict": verdict,
                    "feedback": feedback,
                }
                results.append(tc_res)

                time_used = max(time_used, tc_res["time_used"])
                memory_used = max(memory_used, tc_res["memory_used"])

                # Live update after each test case
                await _write_live(redis, submission_id, {
                    "status": "P", "score": total_score, "max_score": max_score,
                    "time_used": time_used, "memory_used": memory_used,
                    "results": results, "judger_name": judger_name,
                })

                if verdict != "AC":
                    group_passed = False
                    break

            if group_passed:
                total_score += st_points

        # ---- Done ----
        await redis.rpush("results", json.dumps({
            "submission_id": submission_id,
            "status": "D",
            "score": total_score,
            "max_score": max_score,
            "time_used": time_used,
            "memory_used": memory_used,
            "results": results,
            "error": None,
            "judger_name": judger_name,
        }))
        await _write_live(redis, submission_id, {
            "status": "D", "score": total_score, "max_score": max_score,
            "time_used": time_used, "memory_used": memory_used,
            "results": results, "judger_name": judger_name,
        })

    except Exception as e:
        await redis.rpush("results", json.dumps({
            "submission_id": submission_id,
            "status": "D", "score": 0, "max_score": 0,
            "time_used": 0, "memory_used": 0,
            "results": [{"verdict": "IE", "feedback": f"Judge error: {e}", "time_used": 0, "memory_used": 0}],
            "error": str(e), "judger_name": judger_name,
        }))
        await _write_live(redis, submission_id, {
            "status": "D", "score": 0, "max_score": 0,
            "time_used": 0, "memory_used": 0,
            "results": [{"verdict": "IE", "feedback": f"Judge error: {e}", "time_used": 0, "memory_used": 0}],
            "judger_name": judger_name,
        })
    finally:
        user.cleanup()
        shutil.rmtree(judge_dir, ignore_errors=True)
        await redis.close()
