import os
import shutil
import subprocess

from cxx import CXXFLAGS_O0

TESTLIB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "testlib.h")


def compile_cpp(source: str, output_path: str, work_dir: str, flags: list[str] | None = None) -> bool:
    """Biên dịch mã nguồn C++ (code của đề bài dùng CXXFLAGS_O0)."""
    flags = flags or CXXFLAGS_O0

    src_path = os.path.join(work_dir, "_src.cpp")
    with open(src_path, "w", encoding="utf-8") as f:
        f.write(source)

    if os.path.exists(TESTLIB_PATH):
        shutil.copy2(TESTLIB_PATH, os.path.join(work_dir, "testlib.h"))

    cmd = ["g++", *flags, "-DONLINE_JUDGE", src_path, "-o", output_path]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return False
    return proc.returncode == 0 and os.path.exists(output_path)


def run_trusted(exec_path: str, input_path: str, output_path: str, time_limit: float) -> dict:
    """Chạy chương trình tin cậy (như file đáp án chuẩn)."""
    try:
        with open(input_path, "r") as inf, open(output_path, "w") as outf:
            subprocess.run([exec_path], stdin=inf, stdout=outf, timeout=time_limit + 5)
        return {"status": "OK"}
    except subprocess.TimeoutExpired:
        return {"status": "TLE"}
    except Exception as e:
        return {"status": "IE", "error": str(e)}


def run_generator(exec_path: str, arg: str, output_path: str, time_limit: float) -> dict:
    """Chạy sinh dữ liệu test (Generator) với một tham số."""
    try:
        with open(output_path, "w") as outf:
            subprocess.run([exec_path, str(arg)], stdout=outf, timeout=time_limit)
        return {"status": "OK"}
    except subprocess.TimeoutExpired:
        return {"status": "TLE"}
    except Exception as e:
        return {"status": "IE", "error": str(e)}


def run_validator(exec_path: str, input_path: str, time_limit: float) -> dict:
    """Chạy validator (testlib) lên input vừa sinh. Exit code 0 = hợp lệ."""
    try:
        with open(input_path, "r") as inf:
            proc = subprocess.run(
                [exec_path], stdin=inf, capture_output=True, text=True, timeout=time_limit
            )
        if proc.returncode == 0:
            return {"status": "OK"}
        return {
            "status": "INVALID",
            "error": proc.stderr.strip() or proc.stdout.strip() or "Invalid input",
        }
    except subprocess.TimeoutExpired:
        return {"status": "TLE"}
    except Exception as e:
        return {"status": "IE", "error": str(e)}


def run_checker(
    exec_path: str,
    input_path: str,
    output_path: str,
    expected_path: str,
    time_limit: float,
) -> dict:
    """Chạy checker (testlib): checker <input> <output> <answer>. Exit 0 = AC."""
    try:
        with open(input_path, "r") as inf, open(output_path, "r") as ouf, open(expected_path, "r") as anf:
            proc = subprocess.run(
                [exec_path, input_path, output_path, expected_path],
                stdin=inf,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=time_limit,
            )
        if proc.returncode == 0:
            return {"status": "OK"}
        return {
            "status": "WA",
            "error": (proc.stderr or "").strip() or (proc.stdout or "").strip() or None,
        }
    except subprocess.TimeoutExpired:
        return {"status": "TLE"}
    except Exception as e:
        return {"status": "IE", "error": str(e)}
