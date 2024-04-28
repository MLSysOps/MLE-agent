import os
import questionary
from rich.console import Console

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

from agent.utils import *
from agent.types import Step
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
        self.target_
        self.target_source = None

    def ask(self, question):
        """
        Ask a question.
        :param question: the question to ask.
        :return: the answer.
        """
        return questionary.text(question).ask()

    def ask_choice(self, question, choices):
        """
        Ask a choice question.
        :param question: the question to ask.
        :param choices: the choices to choose from.
        :return: the answer.
        """
        return questionary.select(question, choices).ask()

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

        self.chat_history.extend(
            [
                {"role": 'system', "content": prompt},
                {"role": 'user', "content": user_requirement}
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

        return self.target_source

    def gen_task_content(self):
        """
        Generate the content of the current task.
        :return: the content of the task.
        """
        prompt = f"""
        You are an Machine learning engineer, and you are currently working on an ML project using {self.project_state.lang} as the primary language.
        Now are are given a user requirement to generate a code script for the current task.
        
        Current task: {self.step.step}:{self.step.name}
        
        Output format should be:
        
        Code: {{code}}
        
        """

        self.chat_history.extend(
            [
                {"role": 'system', "content": prompt},
                {"role": 'user', "content": ""}
            ]
        )

        with self.console.status("Generating code script..."):
            completion = self.agent.completions(self.chat_history, stream=False)
            code = extract_code(completion.choices[0].message.content)

        return code

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
                    self.console.print(f"The generated file name is: {self.gen_file_name(requirements)}")

            for task in self.step.tasks:
                pass

            is_running = False
