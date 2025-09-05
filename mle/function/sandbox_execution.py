"""
Tools for secure code execution using E2B sandbox.
"""

import os
from typing import Optional, Callable, Any
from collections import deque

try:
    from e2b_code_interpreter import Sandbox
    E2B_AVAILABLE = True
except ImportError:
    E2B_AVAILABLE = False
    Sandbox = None


class SandboxExecutor:
    """
    A secure sandbox executor using E2B for isolated code execution.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the sandbox executor.

        Args:
            api_key: E2B API key. If not provided, will try to read from E2B_API_KEY env var.
        """
        if not E2B_AVAILABLE:
            raise ImportError(
                "e2b-code-interpreter is not installed. "
                "Please install it with: pip install e2b-code-interpreter>=2.0.0"
            )

        self.api_key = api_key or os.getenv("E2B_API_KEY")
        if not self.api_key:
            raise ValueError(
                "E2B API key is required. Please set E2B_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.sandbox = None
        self._stdout_buffer = []
        self._stderr_buffer = []

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def start(self):
        """Start the sandbox if not already started."""
        if not self.sandbox:
            self.sandbox = Sandbox(api_key=self.api_key)

    def close(self):
        """Close the sandbox if open."""
        if self.sandbox:
            self.sandbox.close()
            self.sandbox = None

    def _on_stdout(self, stdout: str):
        """Callback for stdout output."""
        self._stdout_buffer.append(stdout)
        print(stdout, end='')

    def _on_stderr(self, stderr: str):
        """Callback for stderr output."""
        self._stderr_buffer.append(stderr)
        print(stderr, end='')

    def execute_command(self, command: str, max_lines: int = 30) -> str:
        """
        Execute a command in the sandbox.

        This method is designed to be compatible with the existing execute_command function
        in mle/function/execution.py, maintaining the same interface and return format.

        Args:
            command: The command to execute
            max_lines: Maximum number of output lines to return

        Returns:
            A string with exit code and output in the same format as the original function
        """
        if not self.sandbox:
            self.start()

        # Clear buffers
        self._stdout_buffer.clear()
        self._stderr_buffer.clear()

        try:
            # Execute the command in the sandbox with output callbacks
            execution = self.sandbox.run_code(
                command,
                on_stdout=self._on_stdout,
                on_stderr=self._on_stderr
            )

            # Determine exit code based on error status
            exit_code = 1 if execution.error else 0

            # Combine stdout and stderr
            output_lines = []

            # Add stdout
            if self._stdout_buffer:
                output_lines.extend(self._stdout_buffer)

            # Add stderr
            if self._stderr_buffer:
                output_lines.extend(self._stderr_buffer)

            # Add execution results if available
            if hasattr(execution, 'results') and execution.results:
                output_lines.extend(str(execution.results).split('\n'))

            # Add error message if present
            if execution.error:
                output_lines.append(f"Error: {execution.error}")

            # Join all output
            full_output = ''.join(output_lines)

            # Limit output lines similar to the original function
            lines = full_output.split('\n')
            if len(lines) > max_lines:
                # Use deque to efficiently get the last N lines
                output_buffer = deque(lines, maxlen=max_lines)
                limited_output = '\n'.join(output_buffer)
                return f"Exit code: {exit_code}\nOutput (last {max_lines} lines):\n{limited_output}"
            else:
                return f"Exit code: {exit_code}\nOutput:\n{full_output}"

        except Exception as e:
            return f"Error running command in sandbox: {str(e)}"

    def is_available(self) -> bool:
        """Check if the sandbox is available and properly configured."""
        return E2B_AVAILABLE and bool(self.api_key)


def execute_in_sandbox(command: str, max_lines: int = 30, api_key: Optional[str] = None) -> str:
    """
    Convenience function to execute a single command in a sandbox.

    Args:
        command: The command to execute
        max_lines: Maximum number of output lines to return
        api_key: Optional E2B API key

    Returns:
        Command output in the same format as mle/function/execution.py
    """
    with SandboxExecutor(api_key=api_key) as executor:
        return executor.execute_command(command, max_lines)


def check_sandbox_availability() -> bool:
    """
    Check if E2B sandbox is available and configured.

    Returns:
        True if e2b-code-interpreter is installed and API key is set
    """
    if not E2B_AVAILABLE:
        return False

    api_key = os.getenv("E2B_API_KEY")
    return bool(api_key)