from agent.utils import read_file_to_string
from .base_agent import BaseAgent
import subprocess


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

    def run_command_error_tolerant(self, command):
        """
        Run a command in the shell, print the output and error logs, and return the results.
        :param command: Command to run.
        :return: A tuple containing the output, error, and exit status.
        """
        try:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            output, error = process.communicate()
            exit_code = process.wait()

            print(f"Running command: {command}")
            print(f"Output:\n{output}")
            print(f"Error:\n{error}")

            return output, error, exit_code
        except Exception as e:
            print(f"Exception occurred while running command: {command}")
            print(str(e))
            return "", str(e), -1

    def invoke(self, requirement, max_attempts: int = 3):
        debug_success = False

        entry_file = self.project.entry_file
        command = f"python {entry_file}"
        with self.console.status(f"Running the code script with command: {command}"):
            run_log, error_log, exit_code = self.run_command_error_tolerant(command)

        if exit_code != 0:
            for attempt in range(max_attempts):
                self.console.log("Debugging the code script...")

                existing_code = read_file_to_string(entry_file)

                user_prompt = f"""
                Task Requirements: {requirement}
                Existing Code: {existing_code}
                Error Log: {run_log}
                """

                self.chat_history.extend(
                    [
                        {"role": 'system', "content": self.code_debug()},
                        {"role": 'user', "content": user_prompt}
                    ]
                )

                code = self.handle_streaming()

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
