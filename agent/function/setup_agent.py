import json
import questionary

from rich.console import Console

from agent.types import Plan
from agent.utils import preprocess_json_string
from agent.utils.system import run_command


class SetupAgent:
    """
    The SetupAgent class.
    """

    def __init__(self, llm_agent):
        self.agent = llm_agent

        self.console = Console()

    def pmpt_code_dependency(self) -> str:
        return """
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

    def dependency_generator(self, code):
        """
        Generate the dependencies for the project plan.
        """
        chat_history = [
            {"role": 'system', "content": self.pmpt_code_dependency()},
            {"role": 'user', "content": code}
        ]
        print(self.agent.query(chat_history))
        return json.loads(preprocess_json_string(self.agent.query(chat_history)))

    def invoke(self, code):
        """
        Invoke the agent.
        """
        with self.console.status("Guessing and preparing the dependencies for the project plan..."):
            install_commands = self.dependency_generator(code).get('commands')
            dependencies = self.dependency_generator(code).get('dependencies')
            self.console.log(f"[cyan]Will install the following dependencies:[/cyan] {dependencies}")

        # confirm the installation.
        confirm_install = questionary.confirm("Are you sure to install the dependencies?").ask()
        if confirm_install:
            run_command(install_commands)
        else:
            self.console.log("Skipped the dependencies installation.")
