import json
import questionary

from rich.console import Console

from agent.types import Plan
from agent.utils import preprocess_json_string
from agent.utils.system import run_command
from agent.utils.prompt import pmpt_code_dependency


class SetupAgent:
    """
    The SetupAgent class.
    """

    def __init__(self, llm_agent, plan: Plan):
        self.agent = llm_agent
        self.plan = plan

        self.console = Console()

    def dependency_generator(self):
        """
        Generate the dependencies for the project plan.
        """
        chat_history = [
            {"role": 'system', "content": pmpt_code_dependency()},
            {"role": 'user', "content": json.dumps(self.plan.dict())}
        ]
        return json.loads(preprocess_json_string(self.agent.query(chat_history)))

    def invoke(self):
        """
        Invoke the agent.
        """
        with self.console.status("Guessing and preparing the dependencies for the project plan..."):
            install_commands = self.dependency_generator().get('commands')
            dependencies = self.dependency_generator().get('dependencies')
            self.console.log(f"[cyan]Will install the following dependencies:[/cyan] {dependencies}")

        # confirm the installation.
        confirm_install = questionary.confirm("Are you sure to install the dependencies?").ask()
        if confirm_install:
            run_command(install_commands)
        else:
            self.console.log("Skipped the dependencies installation.")
