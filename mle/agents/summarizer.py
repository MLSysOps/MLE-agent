import json
from rich.console import Console

from mle.function import *
from mle.integration import GitHubIntegration


class SummaryAgent:

    def __init__(self, model, github_repo: str, console=None):
        """
        SummaryAgent: summary the workspace provided by the user.

        Args:
            model: the model to use.
            github_repo: the github repo to summarize.
            console: the console to use.
        """
        self.report = None
        self.model = model
        self.chat_history = []
        self.github = GitHubIntegration(github_repo)
        self.console = console
        if not self.console:
            self.console = Console()
        self.sys_prompt = """
        You are a software expert tasked with summarizing the Github project provided by the user. The project may
         contain the dataset, the source code, and the documentation, etc.

        Your capabilities include:

        1. You need to summarize the basic project information, including the project name, the project description,
            the programming language, etc. 
        2. You need to further analyze the project structure and the README file to understand the project purpose. And 
         give a deep understanding of the project description.
        3. You need to analyze the issue list, summarize and infer the project goal and target, and roadmap.
        4. You should read the source code and understand the code structure, and the main functions if necessary. For
         the dataset, you'd better give a brief introduction to the dataset.
         
        You may need the following functions to get necessary information:
        
        1. `read_project_structure` to read the project structure and filenames.
        2. `read_project_readme` to search and read the README file.
        3. `read_project_issues` to read the project issues.
        4. `read_project_source_code` to read the source code for a specific file, if you find it necessary.
        """
        self.json_mode_prompt = """

        JSON Output Format:

        {
            "project_summary": "The project is a ...",
            "project_goal": "The project aims to ...",
            "dataset": [{"name": "description..."}, {"name": "description..."}...],
            "project_type": "frontend application",
            "roadmap": ["The project will ...", "The project will ..."],
        }

        """
        self.functions = [
            schema_preview_csv_data
        ]

        self.sys_prompt += self.json_mode_prompt
        self.chat_history.append({"role": 'system', "content": self.sys_prompt})

    def summary(self):
        """
        Handle the query from the model query response.
        Args: None
        """
        with self.console.status("MLE Advisor is summarizing the project..."):
            self.chat_history.append({"role": "user", "content": ""})  # TODO
            text = self.model.query(
                self.chat_history,
                function_call='auto',
                functions=self.functions,
                response_format={"type": "json_object"}
            )

            self.chat_history.append({"role": "assistant", "content": text})
            summary = json.loads(text)

        return summary
