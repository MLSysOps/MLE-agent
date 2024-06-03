import os
import subprocess
import sys

from .base import BaseAgent
from .search_agent import SearchAgent
from agent.utils import Config, read_file_to_string

config = Config()


class ReflectAgent(BaseAgent):
    def run_command_error_tolerant(self, command):
        """
        Run a command in the shell, print the output and error logs in real time, and return the results.
        :param command: Command to run.
        :return: A tuple containing the output, error, and exit status.
        """
        os.chdir(self.project.path)
        output_log = ""
        error_log = ""
        try:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            while True:
                output_line = process.stdout.readline()
                if output_line:
                    print(output_line, end='')
                    output_log += output_line

                error_line = process.stderr.readline()
                if error_line:
                    print(f"{error_line}", end='', file=sys.stderr)
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
        pmpt_code_debug = f"""
        You are a Machine Learning engineer tasked with debugging a script.
        Your goal is to modify the code so that it meets the task requirements and runs successfully.
        You should modify the existing code based on the user's requirements, logs, and web search results.

        The output format should only with the updated code:

        Code: {{code}}
        """

        debug_success = False
        entry_file = self.project.entry_file
        command = f"python {os.path.basename(entry_file)}"
        with self.console.status(f"Running the code script with command: {command}."):
            run_log, error_log, exit_code = self.run_command_error_tolerant(command)

        if exit_code != 0:
            enable_web_search = False if config.read().get('general').get('search_engine') == "no_web_search" else True
            search_agent = SearchAgent(enable_web_search)

            for attempt in range(max_attempts):
                self.console.log("Debugging the code script...")

                existing_code = read_file_to_string(entry_file)
                search_results = search_agent.invoke(error_log)

                user_prompt = f"""
                Task Requirements: {requirement}
                Existing Code: {existing_code}
                Log: {run_log} {error_log}
                Web Search: {search_results}
                """

                self.chat_history.extend(
                    [
                        {"role": 'system', "content": pmpt_code_debug},
                        {"role": 'user', "content": user_prompt}
                    ]
                )

                self.handle_streaming()
                with self.console.status(f"Running the code script..."):
                    run_log, error_log, exit_code = self.run_command_error_tolerant(command)

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
