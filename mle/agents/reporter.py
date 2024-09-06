import json
from rich.console import Console
from time import gmtime, strftime


class ReportAgent:

    def __init__(self, model, console=None):
        """
        ReportAgent: generate the report based on the information provided by the user.

        Args:
            model: the model to use.
            console: the console to use.
        """
        self.report = None
        self.knowledge = None
        self.model = model
        self.chat_history = []
        self.console = console
        if not self.console:
            self.console = Console()
        self.sys_prompt = """
        You are writing a weekly progress report for an engineer working on a project. Your capabilities include:
        
        1. Based on the user's input information, you need to organize the information and generate more details from the
            user's perspective.
        2. You need to generate a section called "Development Progress" based on the user's Github
            summary given by the user, do not use the commit messages directly.
        3. You need to generate a section called "Communication / Design Progress" based on the user's Google Calendar
            events (if any). Not all events are related to the project but you need to filter out the related ones.
        4. You need to generate a section called "Development To-do" based on the user's Github information, and the
            task priority, with the highest priority first and generate more details.
        5. You need to generate a section called "Communication / Design To-do" based on the user's future
            Google Calendar events (if any).
        6. You need to generate a section called "Existing Hard Parts" to summarize/infer the hard parts of the project.
        7. Based on the hard parts and the project information, you need to generate a section called
            "Require Manager' / Others’ help", to indicate the parts that may need help.
        8. You can generate as more as possible details to make sure the report is informative and has great progress.
        
        """
        self.json_mode_prompt = """

        JSON Output Format:

        {
            "project_okr": "if user provides the ORKs, put there. Otherwise, put an empty string",
            "business_goal": ["The project aims to build an image classification model...", ...],
            "dev_progress": ["implemented the data collection Python function...", ...],
            "communicate_progress": ["Meeting with the design team to discuss the new feature...", ...],
            "dev_todo": [{"task": "fix ...", "description": ..., "priority": "high"}, {"task": "support ..."," description": ..., "priority": "medium"}, ...],
            "communicate_todo": [{"task": "seek helps from ...", "priority": "high"},
             {"task": "meet with ...", "priority": "low"} ...],
            "hard_parts": ["The project may face the challenge of ...", ...],
            "require_manager_help": ["The project needs help from the design team to ...", ...],
            "suggestions_to_user": ["Increase more meeting with design team...", ...],
            "reference": [{"title": "xxxx", "link":"https://arxiv.org/abs/xxx.xxxx"}, {"title": "xxx", "link": "https://github.com/xxx"}, ...],
        }

        """
        self.sys_prompt += self.json_mode_prompt
        self.chat_history.append({"role": 'system', "content": self.sys_prompt})

    def process_knowledge(self, github_summary: dict, calendar_events: list = None, okr: str = None):
        """
        Process the knowledge to generate the report.

        Args:
            github_summary: the summary of the GitHub project.
            calendar_events: the Google Calendar events.
            okr: the OKR of the project.
        """
        info_prompt = f"""
# Project Overview

## The username: {github_summary.get('username')}\n
## The repository: {github_summary.get('github_repo')}\n
## Technology stack: {github_summary.get('tech_stack')}\n
## The project summary: {github_summary.get('summary')}\n
"""
        if okr:
            info_prompt += f"\n## The project's OKR: \n"
            info_prompt += f"{okr}\n"

        info_prompt += f"\n## The project's business goal: \n"
        for goal in github_summary.get("business_goal", []):
            info_prompt += f"- {goal}\n"

        if github_summary.get("dataset"):
            info_prompt += f"\n## The project's datasets: \n"
            for dataset in github_summary.get("dataset"):
                info_prompt += f"- {dataset['name']}: {dataset['description']}\n"

        info_prompt += f"\n## The project's roadmap: \n"
        for task in github_summary.get("roadmap", []):
            info_prompt += f"- {task['task']} ({task['priority']})\n"

        info_prompt += f"\n## The project's hard parts: \n"
        for part in github_summary.get("hard_parts", []):
            info_prompt += f"- {part}\n"

        info_prompt += f"\n## The project's related work: \n"
        for work in github_summary.get("related_work", []):
            info_prompt += f"- {work['title']} ({work['link']})\n"

        activities = github_summary.get("user_activity")
        info_prompt += f"""
# User's Activity (from {activities['period']['start']} to {activities['period']['end']})

"""

        info_prompt += f"""
## Contributions:\n
- Commits: {activities['summary']['total_commits']}
- Pull Requests: {activities['summary']['total_pull_requests']}
- Issues: {activities['summary']['total_issues']}\n
"""

        info_prompt += f"## The user's commits: \n"
        for commit in activities['commits']['messages']:
            info_prompt += f"- {commit}"

        info_prompt += f"\n## The user's pull requests: \n"
        for pr in activities['pull_requests']['details']:
            info_prompt += f"- {pr['title']} ({pr['status']})"

        info_prompt += f"\n## The user's issues: \n"
        for issue in activities['issues']['details']:
            info_prompt += f"- {issue['title']}"

        if calendar_events:
            info_prompt += f"\n## The user's calendar events:\n"
            for event in calendar_events:
                info_prompt += (f"- Title: {event['title']}\n"
                                f" Time: ({event['start_time']} - {event['end_time']})\n"
                                f" Description: {event['description']}\n"
                                f" Organizer: {event['organizer']['email']}\n")

        self.knowledge = info_prompt
        return info_prompt

    def gen_report(self, github_summary: dict, calendar_events: list = None, okr: str = None):
        """
        Handle the query from the model query response.
        Args:
            github_summary: the summary of the GitHub project.
            calendar_events: the Google Calendar
            okr: the OKR of the project.
        """
        with self.console.status("MLE reporter is writing the progress report..."):
            self.chat_history.append(
                {
                    "role": "user",
                    "content": self.process_knowledge(github_summary, calendar_events, okr)
                }
            )
            text = self.model.query(
                self.chat_history,
                response_format={"type": "json_object"}
            )

            self.chat_history.append({"role": "assistant", "content": text})
            # save the dict into a local files
            today = strftime("%Y_%m_%d", gmtime())
            result_dict = json.loads(text)
            with open(f'progress_report_{today}.json', 'w') as f:
                json.dump(result_dict, f)
            return result_dict
