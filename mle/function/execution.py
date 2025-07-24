"""
Tools to execute functions, acquire runtime logs.
"""
from __future__ import annotations

import subprocess
from collections import deque


def execute_command(
    command: str,
    max_lines: int = 30,
    cwd: str = None,
    raw: bool = False,
) -> str | dict:
    """
    Run a command in the shell and return the outputs, errors, and exit status,
    limiting the output to a specified number of most recent lines.

    Args:
        command (str): The input command to run.
        max_lines (int): Maximum number of output lines to keep. Defaults to 100.
        cwd (str): The working directory to run the command in. Defaults to None (current directory).
        raw (bool): If True, returns raw dict of outputs instead of a formatted string.

    Return: A string of the exit status and the limited output (most recent lines).
    """
    try:
        process = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=cwd
        )
        if max_lines > 0:
            stdout_lines = deque(maxlen=max_lines)
            stderr_lines = deque(maxlen=max_lines)
        else:
            stdout_lines = []
            stderr_lines = []

        while True:
            stdout_line = process.stdout.readline()
            stderr_line = process.stderr.readline()
            if stdout_line:
                stdout_lines.append(stdout_line.rstrip())

            if stderr_line:
                stderr_lines.append(stderr_line.rstrip())

            if not stdout_line and not stderr_line and process.poll() is not None:
                break

        exit_code = process.wait()

        result = {
            "exit_code": exit_code,
            "stdout": "\n".join(stdout_lines),
            "stderr": "\n".join(stderr_lines),
            "max_lines": max_lines,
        }

        if raw:
            return result
        else:
            formatted = [f"Exit code: {exit_code}"]
            stderr_clip_msg, stdout_clip_msg = "", ""
            if exit_code != 0 and 0 < max_lines == len(stderr_lines):
                stderr_clip_msg = "(last " + str(max_lines) + ")"
            if exit_code == 0 and 0 < max_lines == len(stdout_lines):
                stdout_clip_msg = "(last " + str(max_lines) + ")"

            if stdout_lines:
                formatted.append(f"\n--- STDOUT {stderr_clip_msg} ---\n{result['stdout']}")
            if stderr_lines:
                formatted.append(f"\n--- STDERR {stdout_clip_msg} ---\n{result['stderr']}")
            return "\n".join(formatted)

    except Exception as e:
        if raw:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "max_lines": max_lines,
            }
        else:
            return f"Error executing command '{command}': {str(e)}"
