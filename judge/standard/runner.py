import os
import subprocess


def compile_cpp(source: str, output_path: str, work_dir: str) -> bool:
    """Biên dịch mã nguồn C++."""
    src_path = os.path.join(work_dir, "_src.cpp")
    with open(src_path, "w", encoding="utf-8") as f:
        f.write(source)

    cmd = [
        "g++", "-std=c++14", "-Wall", "-DONLINE_JUDGE", "-O2",
        "-lm", "-fmax-errors=5", "-march=native", "-s", "-Wl,-z,stack-size=66060288", "-I", ".",
        src_path, "-o", output_path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
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


def run_generator(exec_path: str, seed: int, output_path: str, time_limit: float) -> dict:
    """Chạy sinh dữ liệu test (Generator)."""
    try:
        with open(output_path, "w") as outf:
            subprocess.run([exec_path, str(seed)], stdout=outf, timeout=time_limit)
        return {"status": "OK"}
    except subprocess.TimeoutExpired:
        return {"status": "TLE"}
    except Exception as e:
        return {"status": "IE", "error": str(e)}