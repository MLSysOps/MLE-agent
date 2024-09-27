import sys
import json
from rich.console import Console

from mle.function import *
from mle.utils import get_config, print_in_box, WorkflowCache


class ChatAgent:

    def __init__(self, model, working_dir='.', console=None):
        """
        ChatAgent assists users with planning and debugging ML projects.

        Args:
            model: The machine learning model used for generating responses.
        """
        config_data = get_config()

        self.model = model
        self.chat_history = []
        self.working_dir = working_dir
        self.cache = WorkflowCache(working_dir, 'baseline')

        self.console = console
        if not self.console:
            self.console = Console()

        self.sys_prompt = f"""
        You are a programmer working on an Machine Learning task using Python.
        You are currently working on: {self.working_dir}.

        Your can leverage your capabilities by using the specific functions listed below:

        1. Creating project structures based on the user requirement using function `create_directory`.
        2. Writing clean, efficient, and well-documented code using function `create_file` and `write_file`.
        3. Exam the project to re-use the existing code snippets as much as possible, you may need to use
         functions like `list_files`, `read_file` and `write_file`.
        4. Writing the code into the file when creating new files, do not create empty files.
        5. Use function `preview_csv_data` to preview the CSV data if the task include CSV data processing.
        6. Decide whether the task requires execution and debugging before moving to the next or not.
        7. Generate the commands to run and test the current task, and the dependencies list for this task.
        8. You only write Python scripts, don't write Jupiter notebooks which require interactive execution.
        """
        self.search_prompt = """
        9. Performing web searches use function `web_search` to get up-to-date information or additional context.
        """

        self.functions = [
            schema_read_file,
            schema_create_file,
            schema_write_file,
            schema_list_files,
            schema_create_directory,
            schema_search_arxiv,
            schema_search_papers_with_code,
            schema_web_search,
            schema_execute_command,
            schema_preview_csv_data
        ]

        if config_data.get('search_key'):
            self.functions.append(schema_web_search)
            self.sys_prompt += self.search_prompt

        if not self.cache.is_empty():
            dataset = self.cache.resume_variable("dataset")
            ml_requirement = self.cache.resume_variable("ml_requirement")
            advisor_report = self.cache.resume_variable("advisor_report")
            self.sys_prompt += f"""
            The overall project information: \n
            {'Dataset: ' + dataset if dataset else ''} \n
            {'Requirement: ' + ml_requirement if ml_requirement else ''} \n
            {'Advisor: ' + advisor_report if advisor_report else ''} \n
            """

        self.chat_history.append({"role": 'system', "content": self.sys_prompt})

    def greet(self):
        """
        Generate a greeting message to the user, including inquiries about the project's purpose and
        an overview of the support provided. This initializes a collaborative tone with the user.
        
        Returns:
            str: The generated greeting message.
        """
        system_prompt = """
        You are a Chatbot designed to collaborate with users on planning and debugging ML projects.
        Your goal is to provide concise and friendly greetings within 50 words, including:
        1. Infer about the project's purpose or objective.
        2. Summarize the previous conversations if it existed.
        2. Offering a brief overview of the assistance and support you can provide to the user, such as:
           - Helping with project planning and management.
           - Assisting with debugging and troubleshooting code.
           - Offering advice on best practices and optimization techniques.
           - Providing resources and references for further learning.
        Make sure your greeting is inviting and sets a positive tone for collaboration.
        """
        self.chat_history.append({"role": "system", "content": system_prompt})
        greets = self.model.query(
            self.chat_history,
            function_call='auto',
            functions=self.functions,
        )

        self.chat_history.append({"role": "assistant", "content": greets})
        return greets

    def chat(self, user_prompt):
        """
        Handle the response from the model streaming.
        The stream mode is integrative with the model streaming function, we don't
        need to set it into the JSON mode.

        Args:
            user_prompt: the user prompt.
        """
        text = ''
        self.chat_history.append({"role": "user", "content": user_prompt})
        for content in self.model.stream(
                self.chat_history,
                function_call='auto',
                functions=self.functions,
        ):
            if content:
                text += content
                yield text

        self.chat_history.append({"role": "assistant", "content": text})
