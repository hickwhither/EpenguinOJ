import json
import os
import shutil

import redis.asyncio as aioredis

from checkers import token
from .runner import compile_cpp, run_generator, run_trusted
from .storage import load_problem_and_subtasks, push_final_result, write_live
from submission import Submission


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
        # 1. Khởi tạo trạng thái ban đầu
        await write_live(redis, submission_id, {
            "status": "C", "score": 0, "max_score": 0,
            "time_used": 0, "memory_used": 0, "results": [],
            "judger_name": judger_name,
        })

        # 2. Lấy dữ liệu đề bài
        problem, subtasks = await load_problem_and_subtasks(redis, problem_id)
        if not problem:
            await push_final_result(redis, submission_id, {
                "status": "D", "score": 0, "max_score": 0,
                "time_used": 0, "memory_used": 0,
                "results": [{"verdict": "IE", "feedback": "Problem not found in Redis"}],
                "error": "Problem not found", "judger_name": judger_name,
            })
            return

        # 3. Biên dịch bài nộp người dùng
        user = Submission(submission_id, language, source, box_id)
        if not user.is_compiled:
            await push_final_result(redis, submission_id, {
                "status": "D", "score": 0, "max_score": 0,
                "time_used": 0, "memory_used": 0,
                "results": [{"verdict": "CE", "feedback": user.compile_error}],
                "error": "Compilation Error", "judger_name": judger_name,
            })
            return

        # 4. Biên dịch đáp án chuẩn
        os.makedirs(judge_dir, exist_ok=True)
        answer_src = problem.get("answer", "")
        answer_bin = os.path.join(judge_dir, "ans")
        if not compile_cpp(answer_src, answer_bin, judge_dir):
            await push_final_result(redis, submission_id, {
                "status": "D", "score": 0, "max_score": 0,
                "time_used": 0, "memory_used": 0,
                "results": [{"verdict": "IE", "feedback": "Failed to compile official answer"}],
                "error": "Answer compile failed", "judger_name": judger_name,
            })
            return

        # 5. Khởi tạo thông số vòng chấm
        results = []
        total_score = 0
        max_score = 0
        time_used = 0.0
        memory_used = 0.0

        input_path = os.path.join(user.work_dir, "input")
        output_path = os.path.join(user.work_dir, "output")
        expected_path = os.path.join(judge_dir, "expected")

        await write_live(redis, submission_id, {
            "status": "P", "score": 0, "max_score": 0,
            "time_used": 0, "memory_used": 0, "results": [],
            "judger_name": judger_name,
        })

        # 6. Chạy từng Subtask
        for subtask in subtasks:
            st_points = subtask.get("points", 0)
            max_score += st_points
            st_id = subtask.get('id', '?')

            # Biên dịch Generator cho subtask
            gen_src = subtask.get("generator", "")
            gen_bin = os.path.join(judge_dir, f"gen_{subtask.get('id', '?')}")
            if not compile_cpp(gen_src, gen_bin, judge_dir):
                results.append({"subtask": st_id, "verdict": "IE", "feedback": "Generator compile failed", "time_used": 0, "memory_used": 0})
                await write_live(redis, submission_id, {
                    "status": "P", "score": total_score, "max_score": max_score,
                    "time_used": time_used, "memory_used": memory_used,
                    "results": results, "judger_name": judger_name,
                })
                continue

            group_passed = True
            for seed in subtask.get("seeds", []):
                # Sinh Input
                gen_res = run_generator(gen_bin, seed, input_path, 30.0)
                if gen_res["status"] != "OK":
                    results.append({"subtask": st_id, "verdict": "IE", "feedback": f"Generator: {gen_res.get('error', '')}", "time_used": 0, "memory_used": 0})
                    group_passed = False
                    break

                # Sinh Output chuẩn
                ans_res = run_trusted(answer_bin, input_path, expected_path, problem.get("time_limit", 1.0))
                if ans_res["status"] != "OK":
                    results.append({"subtask": st_id, "verdict": "IE", "feedback": f"Answer: {ans_res.get('error', '')}", "time_used": 0, "memory_used": 0})
                    group_passed = False
                    break

                # Chạy chương trình người dùng
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
                    "subtask": st_id,
                    "time_used": res.get("time_used", 0),
                    "memory_used": res.get("memory_used", 0),
                    "verdict": verdict,
                    "feedback": feedback,
                }
                results.append(tc_res)

                time_used = max(time_used, tc_res["time_used"])
                memory_used = max(memory_used, tc_res["memory_used"])

                # Cập nhật Live Status
                await write_live(redis, submission_id, {
                    "status": "P", "score": total_score, "max_score": max_score,
                    "time_used": time_used, "memory_used": memory_used,
                    "results": results, "judger_name": judger_name,
                })

                if verdict != "AC":
                    group_passed = False
                    break

            if group_passed:
                total_score += st_points

        # 7. Hoàn tất chấm bài thành công
        await push_final_result(redis, submission_id, {
            "status": "D", "score": total_score, "max_score": max_score,
            "time_used": time_used, "memory_used": memory_used,
            "results": results, "error": None, "judger_name": judger_name,
        })

    except Exception as e:
        await push_final_result(redis, submission_id, {
            "status": "D", "score": 0, "max_score": 0,
            "time_used": 0, "memory_used": 0,
            "results": [{"verdict": "IE", "feedback": f"Judge error: {e}", "time_used": 0, "memory_used": 0}],
            "error": str(e), "judger_name": judger_name,
        })
    finally:
        if 'user' in locals():
            user.cleanup()
        shutil.rmtree(judge_dir, ignore_errors=True)
        await redis.close()