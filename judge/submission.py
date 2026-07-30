from __future__ import annotations
import os, shutil
import subprocess

# Language Executor
from languages.python import PythonExecutor
from languages.cpp import CPPExecutor
from languages.text import TextExecutor

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
        
        self.box_dir: str | None = None
        self.meta_path: str | None = None
        self.is_compiled: bool = False
        self.compile_error: str = ""
        self.executable_name: str = ""
        self.executable_path: str = ""

        shutil.rmtree(self.work_dir, ignore_errors=True)
        os.makedirs(self.work_dir, exist_ok=True)
        
        if self.language == "text":
            self.is_compiled = True
            return

        self._compile()

    def _base_cmd(self) -> list[str]:
        return ["isolate", f"--box-id={self.box_id}", "--cg"]

    def _init_box(self) -> None:
        cmd = self._base_cmd() + ["--init"]
        output = subprocess.check_output(cmd, text=True).strip()
        self.box_dir = os.path.join(output, "box")
        self.meta_path = os.path.join(self.work_dir, "meta.txt")

    def _get_meta(self) -> dict[str, str]:
        meta: dict[str, str] = {}
        if not os.path.exists(self.meta_path):
            return meta
            
        with open(self.meta_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if ":" in line:
                    k, v = line.strip().split(":", 1)
                    meta[k] = v.strip()
        return meta

    def _compile(self) -> None:
        src_filename = f"code.{self.executor.file_extension}"
        out_filename = f"code.{self.executor.compiled_file_extension}"
        src_path = os.path.join(self.work_dir, src_filename)
        out_path = os.path.join(self.work_dir, out_filename)
        with open(src_path, "w", encoding="utf-8") as f:
            f.write(self.source_code)
        raw_cmd = self.executor.command.format(source=src_filename, prog=out_filename)
        compile_args = raw_cmd.split()

        try:
            proc = subprocess.run(
                compile_args,
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                timeout=self.compile_time_limit
            )

            if proc.returncode == 0 and os.path.exists(out_path):
                self.is_compiled = True
                self.executable_name = out_filename
                self.executable_path = out_path
            else:
                self.is_compiled = False
                self.compile_error = proc.stderr.strip() or proc.stdout.strip() or "Compilation Failed"
                
        except subprocess.TimeoutExpired:
            self.is_compiled = False
            self.compile_error = f"Compilation Time Limit Exceeded ({self.compile_time_limit}s)"
        except Exception as e:
            self.is_compiled = False
            self.compile_error = f"Internal Compilation Error: {str(e)}"

    def run(
        self,
        input_file_name: str = None,
        output_file_name: str = None,
        time_limit: float = 1.0,    # Seconds
        memory_limit: int = 32768,  # KB
    ) -> dict:
        if not self.is_compiled:
            return {"status": "CE", "error": self.compile_error}
        
        if self.language == "text":
            with open(os.path.join(self.work_dir, "output"), "w", encoding="utf-8") as f:
                f.write(self.source_code)
            return {"status": "OK", "time_used": 0.0, "memory_used": 0.0}
        
        # Chỉ chạy isolate lúc execute (run) code
        self._init_box()
        work_input_path = os.path.join(self.work_dir, "input")
        
        if os.path.exists(work_input_path):
            box_input_name = input_file_name if input_file_name else "input.in"
            shutil.copy2(work_input_path, os.path.join(self.box_dir, box_input_name))
            
        # Copy file đã được compile từ work_dir sang isolate box
        shutil.copy2(self.executable_path, self.box_dir)

        exec_args = ([self.executor.executable] if self.executor.executable else []) + [self.executable_name]
        cmd = self._base_cmd() + [
            f"--meta={self.meta_path}",
            f"--time={time_limit}",
            f"--wall-time={time_limit + 2.0}",
            f"--mem={memory_limit}",
            "--stderr=error.err"
        ]

        # I/O Standard or Files check
        if not input_file_name:
            cmd.append("--stdin=input.in")
        if not output_file_name: 
            cmd.append("--stdout=output.out")
            
        cmd = cmd + ["--run", "--"] + exec_args

        proc = subprocess.run(cmd, capture_output=True, text=True)
        meta = self._get_meta()

        expected_out = output_file_name if output_file_name else "output.out"
        try:
            shutil.copy2(os.path.join(self.box_dir, expected_out), os.path.join(self.work_dir, "output"))
        except FileNotFoundError:
            pass # Thí sinh không tạo file output hoặc code bị lỗi trước khi ghi file
            
        try:
            shutil.copy2(os.path.join(self.box_dir, "error.err"), os.path.join(self.work_dir, "error"))
        except FileNotFoundError:
            pass

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
        shutil.rmtree(self.work_dir, ignore_errors=True)
        subprocess.run(
            self._base_cmd() + ["--cleanup"],
            capture_output=True,
            check=False
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()