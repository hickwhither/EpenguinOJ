from __future__ import annotations
import os, shutil
import subprocess


# Language Executor

class PythonExecutor:
    language_id = "python"
    file_extension = "py"
    compiled_file_extension = "pyc"
    version = "python3 --version"
    command = "/usr/bin/python3 -m compileall -b {source}"
    executable = "/usr/bin/python3"


class CPPExecutor:
    language_id = "cpp"
    file_extension = "cpp"
    compiled_file_extension = "out"
    version = "g++ --version"
    command = "/usr/bin/g++ -std=c++14 -Wall -DONLINE_JUDGE -O2 -lm -fmax-errors=5 -march=native -s {source} -o {prog}"
    executable = ""

class TextExecutor:
    language_id = "text"
    file_extension = "txt"
    compiled_file_extension = "txt"
    version = "cat --version"
    executable = "/usr/bin/cat"


lang_dict = {
    "py": PythonExecutor,
    "cpp": CPPExecutor,
    "text": TextExecutor,
}


# IsolateRunner Class
class Submission:
    def __init__(
        self,
        submission_id: int,
        language: str,
        source_code: str,
        box_id: int = 0,
        compile_time_limit: int = 30,       # Seconds
        compile_memory_limit: int = 32768,  # KB
    ):
        self.submission_id = submission_id
        self.language = language
        self.executor = lang_dict[language]
        self.source_code = source_code
        self.box_id = box_id
        self.compile_time_limit = compile_time_limit
        self.compile_memory_limit = compile_memory_limit
        self.work_dir = f"tmp/{self.submission_id}"


        if self.language == "txt":
            self.is_compiled = True
            return

        self.box_dir: str | None = None
        self.is_compiled: bool = False
        self.compile_error: str = ""

        shutil.rmtree(self.work_dir, ignore_errors=True)
        os.makedirs(self.work_dir, exist_ok=True)
        self._compile()

    def _base_cmd(self) -> list[str]:
        return ["isolate", f"--box-id={self.box_id}", "--cg"]

    def _init_box(self) -> None:
        cmd = self._base_cmd() + ["--init"]
        output = subprocess.check_output(cmd, text=True).strip()
        self.box_dir = os.path.join(output, "box")
        self.meta_path = os.path.join(self.work_dir, f"meta.txt")

    def _get_meta(self) -> dict[str, str]:
        meta: dict[str, str] = {}
        with open(self.meta_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if ":" in line:
                    k, v = line.strip().split(":", 1)
                    meta[k] = v.strip()
        return meta

    def _compile(self) -> None:
        self._init_box()
        src_filename = f"code.{self.executor.file_extension}"
        out_filename = f"code.{self.executor.compiled_file_extension}"

        src_path = os.path.join(self.box_dir, src_filename)
        with open(src_path, "w", encoding="utf-8") as f:
            f.write(self.source_code)

        raw_cmd = self.executor.command.format(source=src_filename, prog=out_filename)
        compile_args = raw_cmd.split()

        isolate_cmd = self._base_cmd() + [
            f"--meta={self.meta_path}",
            f"--time={self.compile_time_limit}",
            f"--mem={self.compile_memory_limit}",
            "--stderr-to-stdout",
            "--processes=0",
            "--run", "--"
        ] + compile_args

        proc = subprocess.run(isolate_cmd, capture_output=True, text=True)
        meta = self._get_meta()

        out_path = os.path.join(self.box_dir, out_filename)

        if proc.returncode == 0 and os.path.exists(out_path):
            self.is_compiled = True
            shutil.copy2(out_path, self.work_dir)
            self.executable_name = out_filename
            self.executable_path = os.path.join(self.work_dir, out_filename)
        else:
            self.is_compiled = False
            self.compile_error = proc.stdout or meta.get("status", "Compilation Failed")

    def run(
        self,
        input: str = None,
        output: str = None,
        time_limit: float = 1.0,    # Giây
        memory_limit: int = 32768,  # KB
    ) -> dict:
        if not self.is_compiled: return
        self._init_box()
        if input:
            shutil.copy2(os.path.join(self.work_dir, "input"), os.path.join(self.box_dir, input))
        else:
            shutil.copy2(os.path.join(self.work_dir, "input"), os.path.join(self.box_dir, "input.in"))
        shutil.copy2(self.executable_path, self.box_dir)

        exec_args = [self.executor.executable] if self.executor.executable else [] + [self.executable_name]

        cmd = self._base_cmd() + [
            f"--meta={self.meta_path}",
            f"--time={time_limit}",
            f"--wall-time={time_limit + 2.0}",
            f"--mem={memory_limit}",
        ]
        if not input: cmd.append("--stdin=input.in")
        if not output: cmd.append("--stdin=output.in")
        cmd = cmd + ["--stderr=error.err", "--run", "--"] + exec_args

        proc = subprocess.run(cmd, capture_output=True, text=True)
        meta = self._get_meta()
        
        shutil.copy2(os.path.join(self.box_dir, "output.out"), os.path.join(self.work_dir, "output"))
        shutil.copy2(os.path.join(self.box_dir, "error.err"), os.path.join(self.work_dir, "error"))

        status = meta.get("status", "OK")
        if status == "TO":
            status = "TLE"
        elif status in {"XX", "FO"}:
            status = "IE"
        elif status in {"SG", "RE"}:
            status = "MLE" if meta.get("exitsig") == "9" else "RTE"
        elif proc.returncode != 0 or meta.get("exitcode", "0") != "0":
            if status == "OK":
                status = "RTE"

        mem_used = float(meta.get("cg-mem") or meta.get("max-rss") or 0)
        time_used = float(meta.get("time", 0) or 0)

        return {
            "status": status,
            "time_used": time_used,
            "memory_used": mem_used
        }

    def cleanup(self) -> None:
        subprocess.run(
            self._base_cmd() + ["--cleanup"],
            capture_output=True,
            check=False
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()