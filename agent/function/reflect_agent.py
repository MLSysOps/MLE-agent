from agent.types import Plan
from rich.console import Console

from agent.utils import run_command, read_file_to_string
from .base_agent import BaseAgent


class ReflectAgent(BaseAgent):

    def code_debug(self,) -> str:
        return f"""
        You are a Machine Learning engineer tasked with debugging a script. Below are the user's requirement, existing
        code and the error logs. Your goal is to modify the code so that it meets the task requirements and
        runs successfully.

        Task Requirements:
        Existing Code:
        Error Log:

        The output format should be:

        Code: {{code}}
        """

    def invoke(self, max_attempts: int = 3):
        # TODO: allow generating the command to run the code script.
        # TODO: allow handling the issues that are not comes from the code script.
        # TODO: allow handling the program timeout.

        debug_success = False

        entry_file = self.plan.entry_file
        command = f"python {entry_file}"
        with self.console.status(f"Running the code script with command: {command}"):
            run_log, exit_code = run_command([command])

        if exit_code != 0:
            for attempt in range(max_attempts):
                self.console.log("Debugging the code script...")

                existing_code = read_file_to_string(entry_file)

                user_prompt = f"""
                Task Requirements: {self.requirement} \n
                Existing Code: {existing_code} \n
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
                    run_log, exit_code = run_command([command])

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

