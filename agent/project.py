import os
from rich.console import Console

from agent.const import CONFIG_PROJECT_FILE
from agent.utils import read_project_state


class Project:
    def __init__(self, project_path: str):
        """
        Project class for MLE agent.
        :param project_path: the path of the project.
        """
        self.console = Console()
        self.project_path = project_path
        config_path = os.path.join(project_path, CONFIG_PROJECT_FILE)
        if os.path.isfile(config_path):
            self.state = read_project_state(os.path.abspath(config_path))
        else:
            self.console.log(f"[red]The project state file {config_path} does not exist.")
            self.state = None

    def __str__(self):
        return f"{self.state.name}: {self.state.description}"
