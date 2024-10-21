"""
Tools to execute functions, acquire runtime logs.
"""

import subprocess
from collections import deque


def execute_command(command: str, max_lines: int = 30):
    """
    Run a command in the shell and return the outputs, errors, and exit status,
    limiting the output to a specified number of most recent lines.

    Args:
        command (str): The input command to run.
        max_lines (int): Maximum number of output lines to keep. Defaults to 100.

    Return: A string of the exit status and the limited output (most recent lines).
    """
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        output_buffer = deque(maxlen=max_lines)

        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            output_buffer.append(line.rstrip())
            print(line, end='')

        exit_code = process.wait()

        limited_output = "\n".join(output_buffer)
        if len(output_buffer) == max_lines:
            return f"Exit code: {exit_code}\nOutput (last {max_lines} lines):\n{limited_output}"
        else:
            return f"Exit code: {exit_code}\nOutput:\n{limited_output}"

    except Exception as e:
        return f"Error running command: {str(e)}"
