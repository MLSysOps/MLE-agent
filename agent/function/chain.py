import os
import questionary
from rich.live import Live
from rich.panel import Panel
from rich.console import Console
from rich.markdown import Markdown

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

from agent.utils import *
from agent.types import Step, Task, Resource
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
        self.chat_history = []
        self.console = Console()
        project_path = config.read()['project']['path']
        self.project_state = read_project_state(os.path.join(project_path, CONFIG_PROJECT_FILE))
        self.project_home = config.read().get('project')['path']
        self.session = PromptSession(
            history=FileHistory(str(os.path.join(self.project_home, CONFIG_TASK_HISTORY_FILE)))
        )
        self.target_source = None
        self.user_requirement = None

    def ask(self, question):
        """
        Ask a question.
        :param question: the question to ask.
        :return: the answer.
        """
        return questionary.text(question).ask()

    def ask_choice(self, question, choices: Resource):
        """
        Ask a choice question.
        :param question: the question to ask.
        :param choices: the choices to choose from.
        :return: the answer.
        """
        source_kind = questionary.select(question, [c.name for c in choices]).ask()
        if source_kind:
            for choice in choices:
                if choice.name == source_kind:
                    if choice.choices:
                        return questionary.select("Please select", choice.choices).ask()

                    return source_kind

    def gen_file_name(self, user_requirement: str):
        """
        Generate a file name.
        :return: the file name.
        """
        prompt = f"""
        You are an Machine learning engineer, and you are currently working on an ML project using {self.project_state.lang} as the primary language.
        Now are are given a user requirement to generate a file name for the current task, note the file suffix (e.g., .py) should be correct.
        
        Output format should be:
        
        File Name: {{name}}
        
        """

        self.user_requirement = user_requirement
        self.chat_history.extend(
            [
                {"role": 'system', "content": prompt},
                {"role": 'user', "content": self.user_requirement}
            ]
        )

        with self.console.status("Generating file name..."):
            completion = self.agent.completions(self.chat_history, stream=False)
            target_name = extract_file_name(completion.choices[0].message.content)
            self.target_source = os.path.join(self.project_state.path, target_name)

        self.console.print(f"The generated file name is: {self.target_source}")
        confirm = questionary.confirm("Do you want to use this name?").ask()
        if not confirm:
            new_name = questionary.text("Please provide a new file name:", default=self.target_source).ask()
            if new_name:
                self.target_source = os.path.join(self.project_state.path, new_name)

        # clear the chat history
        self.chat_history = []

        return self.target_source

    def gen_task_content(self, task: Task):
        """
        Generate the content of the current task.
        :return: the content of the task.
        """
        prompt = f"""
        You are an Machine learning engineer, and you are currently working on an ML project using {self.project_state.lang} as the primary language.
        Please generate a code script for the current task based on following information.
        
        User Requirement: {self.user_requirement}   
        Primary language: {self.project_state.lang}
        Current task: {task.name}
        Task description: {task.description}
        
        Output format should be:
        
        Code: {{code}}
        
        """

        self.chat_history.extend(
            [
                {"role": 'user', "content": prompt}
            ]
        )

        text = ""
        completion = self.agent.completions(self.chat_history, stream=True)

        with Live(console=self.console) as live:
            for token in completion:
                content = token.choices[0].delta.content
                if content:
                    text = text + content
                    live.update(
                        Panel(Markdown(text), title="[bold magenta]MLE Assistant[/]", border_style="magenta"),
                        refresh=True
                    )

                stop_reason = token.choices[0].finish_reason
                if stop_reason == "stop":
                    code = extract_code(text)
                    if code:
                        with open(self.target_source, 'w') as file:
                            file.write(code)
                        self.console.print(f"Code generated to: {self.target_source}")

    def start(self):
        """
        Execute the chain.
        :return: the result of the chain.
        """
        is_running = True
        while is_running:
            # identify the current target source code file.
            if self.target_source is None:
                requirements = self.ask("What are the user requirements for the file name?")
                if requirements:
                    self.target_source = self.gen_file_name(requirements)
                    self.console.print(f"The generated file name is: {self.target_source}")

            # working on the task content.
            task_cur = 0
            for task in self.step.tasks:
                if task_cur < self.project_state.task:
                    continue
                else:
                    self.console.log(f"Working on task {task_cur + 1}/{len(self.step.tasks)}")
                    self.project_state.task = task_cur
                    if task.kind == 'generation':
                        self.gen_task_content(task)
                    elif task.kind == 'multiple_choice':
                        self.ask_choice(task.description, task.resources)

                task_cur += 1
            is_running = False

        update_project_state(self.project_home, self.project_state.dict(exclude_none=True))
