from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel

from agent.types import Task, Project
from agent.utils import Config, read_file_to_string, extract_code, update_project_state

config = Config()


class CodeGenerator:
    def __init__(self, agent, project: Project):
        self.agent = agent
        self.project = project

        self.chat_history = []
        self.console = Console()
        self.project_home = config.read().get('project')['path']

        # TODO: Decide if we need previous Chat history or start a new one.

    def system_pmpt_code_gen_new(self) -> str:
        return f"""
        You are a Machine Learning engineer working on an ML project using {self.project.lang} as the primary language.
        The user requires a new code script for the current task. Please read users requirement and task description
        very carefully and generate a new code script that meets them step by step.
        Please make sure only output code with appropriate comments and documentation.

        The output format should be:

        Code: {{code}}
        """

    def system_pmpt_code_gen_existing(self, code: str) -> str:
        return f"""
        You are a Machine Learning engineer working on an ML project using {self.project.lang} as the primary language.
        The user requires modifications to the existing code to meet the task requirements and finish the project.
        Please use the following information to modify or add new changes to the code to finish the task and project.
        Please think this as a requirement, task and code review and make necessary changes to the code.
        Please make sure only output code with appropriate comments and documentation.
        Please think step by step.

        Existing Code: {code}

        The output format should be:

        Code: {{code}}
        """

    def task_prompt(self, task: Task) -> str:

        # TODO: need to find a better way to read user's requirement

        return f"""
        User Requirement: {self.project.requirement}
        Primary Language: {self.project.lang}
        Current Task: {task.name}
        Task Description: {task.description}

        Make sure to incorporate some MLOps code using some MLOps tools for better ML management and reproducibility
        """

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
                with open(self.project.entry_file, 'w') as file:
                    file.write(code)
                self.console.log(f"Code generated to: {self.project.entry_file}")
        return text

    def gen_code(self, task: Task):
        """
        Generate the content of the current task.
        :param task: the task to work on

        :return: the content of the task.
        """
        entry_file = self.project.entry_file
        sys_prompt = self.system_pmpt_code_gen_new()
        if entry_file:
            existing_code = read_file_to_string(entry_file)
            if existing_code or self.project.plan.current_task <= 1:
                sys_prompt = self.system_pmpt_code_gen_existing(existing_code)
            else:
                self.console.log(
                    f"File {entry_file} not found. "
                    f"Please make sure the script exists or deleting the {entry_file} in the project.yml \n"
                )
                return None

        self.chat_history.extend(
            [
                {"role": 'system', "content": sys_prompt},
                {"role": 'user', "content": self.task_prompt(task)}
            ]
        )

        code = self.handle_streaming()

        return code

    def invoke(self, task_num):
        for task in self.project.plan.tasks:
            if self.project.plan.current_task < task_num:
                self.console.log(f"Working on task: {task.name} ({self.project.plan.current_task + 1}/{task_num})")
                # TODO: add supports for other kind of tasks.
                if task.kind == 'code_generation':
                    result = self.gen_code(task)
                    if result is None:
                        self.console.log("[red]Task failed. Aborting the chain.")
                        return

                self.project.plan.current_task += 1
            update_project_state(self.project)
