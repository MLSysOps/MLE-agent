import json
import questionary

from .base import BaseAgent
from agent.types import DebugEnv
from agent.utils import run_command, preprocess_json_string, update_project_state, read_file_to_string
from agent.hub import load_yml


class SetupAgent(BaseAgent):
    """
    The SetupAgent class.
    """

    def dependency_generator(self, code):
        """
        Generate the dependencies for the project plan.
        """
        pmpt_code_dependency = """
        As an ML project expert, your task is to analyze the user-provided code and detect the necessary dependencies
        required for the project. Based on this analysis, you will generate a list of shell commands that the user can
        execute to install these dependencies.

        Your output should include:
        - A list of detected dependencies.
        - Corresponding shell commands for installing these dependencies.
        - Ensure that these commands are suitable for execution in the user's environment.

        The output must be structured in JSON format to facilitate easy parsing and integration in different environments or tools.

        INPUT:
        Code provided by the user.

        EXAMPLE INPUT:
        import torch
        from transformers import BertModel

        EXPECTED OUTPUT in JSON FORMAT:
        {
            "dependencies": ["torch", "transformers", "build-essential"],
            "commands": ["python -m pip install torch", "pip install transformers", "apt-get install build-essential"]
        }
        """

        chat_history = [
            {"role": 'system', "content": pmpt_code_dependency},
            {"role": 'user', "content": code}
        ]
        return json.loads(preprocess_json_string(self.model.query(chat_history)))

    def invoke(self):
        """
        Invoke the agent.
        """
        source_code = read_file_to_string(self.project.entry_file)
        with self.console.status("Guessing and preparing the dependencies for the project plan..."):
            install_commands = self.dependency_generator(source_code).get('commands')
            dependencies = self.dependency_generator(source_code).get('dependencies')
            self.console.log(f"[cyan]Will install the following dependencies:[/cyan] {dependencies}")

        # confirm the installation.
        confirm_install = questionary.confirm("Are you sure to install the dependencies?").ask()
        if confirm_install:
            run_command(install_commands)
        else:
            self.console.log("Skipped the dependencies installation. You may need to install them manually.")

        # configurate the debug environment.
        self.project.debug_env = questionary.select(
            "Select the debug environment:",
            choices=[DebugEnv.not_running.value, DebugEnv.local.value, DebugEnv.cloud.value]
        ).ask()
        update_project_state(self.project)

        # Ask which cloud service to use
        if self.project.debug_env == DebugEnv.cloud.value:
            self.project.cloud_service = questionary.select(
                "Select the cloud service:",
                choices=["AWS", "GCP", "Azure"]
            ).ask()
