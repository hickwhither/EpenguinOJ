import os
import subprocess
from pathlib import Path
from checkers import token
from submission import Submission


def _safe_read(path: str) -> str:
    if os.path.exists(path):
        with open(path, "r", errors="ignore") as f:
            return f.read(128)
    return ""


def judge(executable, exec_path, problem, box_id=0, work_dir: str | None = None):
    work_dir = work_dir or os.path.join("tmp", "judge", f"box{box_id}")
    Path(work_dir).mkdir(parents=True, exist_ok=True)

    time_used = 0
    memory_used = 0
    test_cases_results = []
    total_score = 0
    max_score = 0

    answer = os.path.join("cache", problem["code"], "answer")
    input_path = os.path.join(work_dir, "input")
    output_path = os.path.join(work_dir, "output")
    answer_path = os.path.join(work_dir, "answer")
    error_path = os.path.join(work_dir, "error")

    for subname, subtask in problem["subtasks"].items():
        group_passed = True
        max_score += subtask["points"]
        generator = os.path.join("cache", problem["code"], subtask["generator"])
        for s in subtask["seeds"]:
            # Run generator and official solution inside this judge worker's work directory.
            with open(input_path, "w") as input_file:
                subprocess.run([generator, str(s)], stdout=input_file)
            with open(input_path, "r") as input_file, open(answer_path, "w") as answer_file:
                subprocess.run([answer], stdin=input_file, stdout=answer_file)

            res = isolate_run(
                executable, exec_path, input_path, output_path, error_path,
                problem.get("time_limit", 2000),
                problem.get("memory_limit", 32768),
                box_id,
                work_dir=work_dir,
            )
            res["subtask"] = subname

            # Verdict
            feedback = token.check(output_path, answer_path)
            res['verdict'] = 'WA' if feedback else 'AC'
            res['feedback'] = feedback
            if res['verdict'] == 'WA':
                group_passed = False
                break
            
            # Time memory
            time_used = max(time_used, res.get('time_used', 0))
            memory_used = max(memory_used, res.get('memory_used', 0))

            # File read
            res['input'] = _safe_read(input_path)
            res['output'] = _safe_read(output_path)
            res['answer'] = _safe_read(answer_path)
            res['error'] = _safe_read(error_path)

            test_cases_results.append(res)
        
        if group_passed:
            total_score += subtask["points"]

    percentage = total_score / max_score if max_score > 0 else 0.0

    return {
        'status': 'D',
        'time_used': time_used,
        'memory_used': memory_used,
        'percentage': percentage,
        'test_cases': test_cases_results
    }



async def process_submission(payload: dict, box_id=0):
    """Hàm xử lý submission (Ví dụ: chấm bài, chấm code, etc.)"""
    submission_id = payload.get("submission_id")
    problem_id = payload.get("problem_id")
    language = payload.get("language")
    source = payload.get("source")
    
    print(f"🚀 Submission#{submission_id} Language:{language} Problem({problem_id})")

    user = Submission(submission_id, language, source, box_id)
    
    user.cleanup()

    print(f"✅ Submission #{submission_id}")

