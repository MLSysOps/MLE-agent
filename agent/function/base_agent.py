from abc import ABC
from agent.types import Plan
from rich.console import Console

from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel

from agent.utils import extract_code, update_project_plan, Config

config = Config()


class BaseAgent(ABC):
    def __init__(self, agent, plan: Plan, requirement: str):
        self.agent = agent
        self.plan = plan
        self.requirement = requirement

        self.chat_history = []
        self.console = Console()
        self.project_home = config.read().get('project')['path']

    def update_project_state(self):
        """
        Update the project state.
        :return: None
        """
        update_project_plan(self.project_home, self.plan.dict(exclude_none=True))
        return self.plan

    def handle_streaming(self):
        """
        Handle the streaming completion.
        :return: the result.
        """
        text = ""
        with Live(console=self.console) as live:
            for token in self.agent.query(self.chat_history):
                if token:
                    text = text + token
                    live.update(
                        Panel(Markdown(text), title="[bold magenta]MLE-Agent[/]", border_style="magenta"),
                        refresh=True
                    )

            code = extract_code(text)
            if code:
                with open(self.plan.entry_file, 'w') as file:
                    file.write(code)
                self.console.log(f"Code generated to: {self.plan.entry_file}")
        return text
