from abc import ABC

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel

from agent.types import Project
from agent.utils import extract_code, Config

config = Config()


class BaseAgent(ABC):
    def __init__(self, model, project: Project):
        self.model = model
        self.project = project
        self.requirement = self.project.requirement

        self.chat_history = []
        self.console = Console()
        self.project_home = config.read().get('project')['path']

    def handle_streaming(self):
        """
        Handle the streaming completion.
        :return: the result.
        """
        text = ""
        with Live(console=self.console) as live:
            for token in self.model.query(self.chat_history):
                if token:
                    text = text + token
                    live.update(
                        Panel(Markdown(text), title="[bold magenta]MLE-Agent[/]", border_style="magenta"),
                        refresh=True
                    )

            code = extract_code(text)
            if code:
                with open(self.project.entry_file, 'w') as file:
                    file.write(code)
                self.console.log(f"Code generated to: {self.project.entry_file}")
        return text
