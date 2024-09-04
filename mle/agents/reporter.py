import json
from rich.console import Console

from mle.function import *
from mle.integration import GitHubIntegration


class ReportAgent:

    def __init__(self, model, console=None):
        """
        ReportAgent: generate the report based on the information provided by the user.

        Args:
            model: the model to use.
            console: the console to use.
        """
        self.report = None
        self.model = model
        self.chat_history = []
        self.console = console
        if not self.console:
            self.console = Console()
        self.sys_prompt = """
        You are writing a progress report for an engineer working on a project. Your capabilities include:
        
        1. Based on the user's input information, you need to organize the information and generate a report.
        2. The first section should be the "Business Goal" to summarize the project's business goal.
        3. You need to generate a section called "Development Progress" based on the user's Github
            summary given by the user. You may need to generate some more details based on the issues/PRs/commits
            to make the report more informative.
        4. You need to generate a section called "Communication / Design Progress" based on the user's Google Calendar
            events given by the user. You may need to generate some more details based on the events to make the report.
        5. You need to generate a section called "Development To-do" based on the user's Github information, and the
            task priority.
        6. You need to generate a section called "Communication / Design To-do" based on the user's future
            Google Calendar events.
        7. You need to generate a section called "Existing Hard Parts" to summarize the hard parts of the project.
        8. Based on the hard parts and the project information, you need to generate a section called
            "Require Manager' / Others’s help", to indicate the parts that need help.
        9. You should put some related work and suggestions in the "Other Progress / Thoughts" section.
        10. You can generate as more as possible details to make sure the report is informative and has great progress.
        
        """
        self.json_mode_prompt = """

        JSON Output Format:

        {
            "project_okr": "if user provides the ORKs, put there. Otherwise, put an empty string",
            "business_goal": ["The project aims to build an image classification model...", ...],
            "dev_progress": ["implemented the data collection Python function...", ...],
            "communicate_progress": ["Meeting with the design team to discuss the new feature...", ...],
            "dev_todo": [{"task": "fix ...", "priority": "high"}, {"task": "support ...", "priority": "medium"}, ...],
            "communicate_todo": [{"task": "seek helps from ...", "priority": "high"},
             {"task": "meet with ...", "priority": "low"} ...],
            "hard_parts": ["The project may face the challenge of ...", ...],
            "require_manager_help": ["The project needs help from the design team to ...", ...],
            "suggestions_to_user": ["Increase more meeting with design team...", ...],
            "reference": ["https://arxiv.org/abs/1409.0575", "https://github.com/MLSysOps/MLE-Agent", ...],
        }

        """
        self.sys_prompt += self.json_mode_prompt
        self.chat_history.append({"role": 'system', "content": self.sys_prompt})

    def process_knowledge(self, github_summary: dict, calendar_events: list):
        """
        Process the knowledge to generate the report.

        Args:
            github_summary: the summary of the Github project.
            calendar_events: the Google Calendar events.
        """

    def gen_report(self, github_summary: dict, calendar_events: list):
        """
        Handle the query from the model query response.
        Args: None
        """
        with self.console.status("MLE summarizer is summarizing the project..."):
            self.chat_history.append(
                {
                    "role": "user",
                    "content": self.process_knowledge(github_summary, calendar_events)
                }
            )
            text = self.model.query(
                self.chat_history,
                response_format={"type": "json_object"}
            )

            self.chat_history.append({"role": "assistant", "content": text})
            summary = json.loads(text)
        return summary
