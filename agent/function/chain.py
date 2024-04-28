import os
from rich.console import Console

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

from agent.types import Step
from agent.utils import Config
from agent.const import CONFIG_TASK_HISTORY_FILE

config = Config()


class Chain:

    def __init__(self, step: Step, llm_agent):
        """
        Chain: the interactive chain of the current ML task.
        :param step: the step of the chain.
        :param llm_agent: the language model agent.
        """
        self.step = step
        self.agent = llm_agent
        self.console = Console()
        self.project_home = config.read().get('project')['path']
        self.session = PromptSession(
            history=FileHistory(str(os.path.join(self.project_home, CONFIG_TASK_HISTORY_FILE)))
        )

    def start(self):
        """
        Execute the chain.
        :return: the result of the chain.
        """
        is_running = True
        while is_running:
            self.console.print(f"[bold]{self.step.name}[/bold]")
            self.console.print(f"{self.step.description}")
            for task in self.step.tasks:
                self.console.print(f"[bold]{task.name}[/bold]")
                self.console.print(f"{task.description}")
                if task.resources:
                    for resource in task.resources:
                        self.console.print(f"[bold]{resource.name}[/bold]")
                        self.console.print(f"{resource.description}")
                        if resource.choice:
                            for choice in resource.choice:
                                self.console.print(f"[bold]{choice}[/bold]")
                if task.functions:
                    for function in task.functions:
                        self.console.print(f"[bold]{function}[/bold]")
            is_running = False
