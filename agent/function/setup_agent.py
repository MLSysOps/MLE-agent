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

    def __init__(self, llm_agent, plan: Plan):
        self.agent = llm_agent
        self.plan = plan

        self.console = Console()

    def pmpt_code_dependency(self) -> str:
        return f"""
        You are an ML project expert that detect which dependencies the user need to install
        to meet the project plan requirements. And generate a list of shell commands to install the dependencies.
    
        - The project is written in.
        - The commands should be in the form of a list.
        - The commands should be able to run in the user's environment.
    
        EXAMPLE OUTPUT in JSON FORMAT:
    
        'commands': ['python -m pip install torch', 'pip install transformers', 'apt-get install build-essential']
        'dependencies': ['torch', 'transformers', 'build-essential']
    
        """

    def dependency_generator(self):
        """
        Generate the dependencies for the project plan.
        """
        chat_history = [
            {"role": 'system', "content": self.pmpt_code_dependency()},
            {"role": 'user', "content": json.dumps(self.plan.dict())}
        ]
        resp = self.agent.completions(chat_history, stream=False)
        results = resp.choices[0].message.content
        return json.loads(preprocess_json_string(results))

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