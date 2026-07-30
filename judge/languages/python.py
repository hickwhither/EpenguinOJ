class PythonExecutor:
    language_id = "python"
    file_extension = "py"
    compiled_file_extension = "pyc"
    version = "python3 --version"
    command = "/usr/bin/python3 -m compileall -b {source}"
    executable = "python3"
    example="print('Hello, world!')"