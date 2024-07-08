"""
Tools to execute functions, acquire runtime logs.
"""

import subprocess


def execute_command(command: str):
    """
    Run multiple commands in the shell and return the outputs, errors, and exit statuses.
    Args:
        command: the list of input commands to run.

    Return: a string of the output, error (if any), and exit status for the command.
    """
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        output = ''
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            output += line
            print(line, end='')

        exit_code = process.wait()
        return f"Exit code: {exit_code} \nOutput: \n{output}"
    except Exception as e:
        return f"Error running command: {str(e)}"
