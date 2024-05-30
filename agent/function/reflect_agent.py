import os
import subprocess
import sys

from agent.utils import read_file_to_string
from .base_agent import BaseAgent


class ReflectAgent(BaseAgent):

    def code_debug(self) -> str:
        return f"""
        You are a Machine Learning engineer tasked with debugging a script. Below are the user's requirements,
        existing code, and error logs. Your goal is to modify the code so that it meets the task requirements and
        runs successfully.

        Task Requirement:
        {{requirement}}

        Existing Code:
        {{existing_code}}

        Run Log:
        {{run_log}}

        The output format should be:

        Code: {{code}}
        """

    def run_command_error_tolerant(self, command, working_dir):
        """
        Run a command in the shell, print the output and error logs in real time, and return the results.
        :param command: Command to run.
        :param working_dir: Directory to execute the command.
        :return: A tuple containing the output, error, and exit status.
        """
        os.chdir(working_dir)  # Change to the appropriate directory
        output_log = ""
        error_log = ""
        try:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            print(f"Running command: {command}")

            # Stream and accumulate stdout and stderr
            while True:
                output_line = process.stdout.readline()
                if output_line:
                    print(output_line, end='')
                    output_log += output_line
                error_line = process.stderr.readline()
                if error_line:
                    print(f"Error: {error_line}", end='', file=sys.stderr)
                    error_log += error_line
                if output_line == '' and error_line == '' and process.poll() is not None:
                    break

            exit_code = process.wait()
            return output_log, error_log, exit_code
        except Exception as e:
            print(f"Exception occurred while running command: {command}")
            print(str(e))
            return "", str(e), -1

    def invoke(self, requirement, max_attempts: int = 3):
        debug_success = False

        entry_file = self.project.entry_file
        working_dir = os.path.dirname(entry_file)
        file_name = os.path.basename(entry_file)
        command = f"python {file_name}"

        with self.console.status(f"Running the code script with command: {command} under {working_dir}"):
            run_log, error_log, exit_code = self.run_command_error_tolerant(command, working_dir)

        if exit_code != 0:
            for attempt in range(max_attempts):
                self.console.log("Debugging the code script...")

                existing_code = read_file_to_string(entry_file)

                user_prompt = f"""
                Task Requirements: {requirement}
                Existing Code: {existing_code}
                Error Log: {run_log} {error_log}
                """

                self.chat_history.extend(
                    [
                        {"role": 'system', "content": self.code_debug()},
                        {"role": 'user', "content": user_prompt}
                    ]
                )

                code = self.handle_streaming()

                with self.console.status(f"Running the code script..."):
                    run_log, error_log, exit_code = self.run_command_error_tolerant(command, working_dir)

                if exit_code == 0:
                    debug_success = True
                    self.console.log("Debugging successful, the code script has been saved.")
                    break

            if not debug_success:
                self.console.log(f"Debugging failed after {max_attempts} attempts.")
                return None
        else:
            self.console.log("The code script has been run successfully.")
            return None
