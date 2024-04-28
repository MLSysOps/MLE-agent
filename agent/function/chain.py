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
        completion = self.agent.completions(self.chat_history, stream=False)
        response = completion.choices[0].message.content

        return extract_file_name(response)

    def start(self):
        """
        Execute the chain.
        :return: the result of the chain.
        """
        is_running = True
        while is_running:
            requirements = self.ask("What are the user requirements for the file name?")
            self.console.print(f"The generated file name is: {self.gen_file_name(requirements)}")
            is_running = False
