import sys
import json
from rich.console import Console

from mle.function import *
from mle.utils import get_config
from mle.utils import print_in_box


def process_summary(summary_dict: dict):
    """
    Process the code summary.
    Args:
        summary_dict: the code summary in a dictionary format.
    """
    return textwrap.dedent(f"""
MLE Developer has finished the task: {summary_dict.get('task')}.\n
Task description: {summary_dict.get('task_description')}\n
{summary_dict.get('message')}\n
Dependencies you are required to run the code: {summary_dict.get('dependency')}\n
Command to run the code: {summary_dict.get('command')}\n
Whether the code is required to execute and debug: {summary_dict.get('debug')}""")


class CodeAgent:

    def __init__(self, model, working_dir='.', console=None, single_file=False):
        """
        CodeAgent: the agent to solve the given coding problems, by planning coding tasks, searching websites,
        and generating code snippets. It does not execute the code, only make use of built-in functions to provides
         the code snippets to solve the problem.

        Args:
            model: the model to use.
            working_dir: the working directory.
            console: the console to use.
            single_file: whether the agent is working on a single file or not.
        """
        config_data = get_config()
        self.code_summary = None
        self.model = model
        self.chat_history = []
        self.working_dir = working_dir

        self.console = console
        if not self.console:
            self.console = Console()

        self.sys_prompt = f"""
        You are a programmer working on an Machine Learning task using Python.
        You are currently working on: {self.working_dir}.

        Your can leverage your capabilities by using the specific functions listed below:

        - Creating project structures based on the user requirement using function `create_directory`.
        - Writing clean, efficient, and well-documented code using function `create_file` and `write_file`.
        - Exam the project to re-use the existing code snippets as much as possible, you may need to use
         functions like `list_files`, `read_file` and `write_file`.
        - Writing the code into the file when creating new files, do not create empty files.
        - Use function `preview_csv_data` to preview the CSV data if the task include CSV data processing.
        - Decide whether the task requires execution and debugging before moving to the next or not.
        - Generate the commands to run and test the current task, and the dependencies list for this task.
        - You only write Python scripts, don't write Jupiter notebooks which require interactive execution.
        """

        if single_file:
            self.sys_prompt = f"""
            You are an expert programmer working on an Machine Learning task using Python.
            You are currently working on: {self.working_dir}.
            
            Your can leverage your capabilities by using the specific functions listed below:
            
            - You should create a single script first, with the complete code inside. You can have multiple functions and classes.
            - Writing clean, efficient, and well-documented code to a script using functions `create_file`.
            - Use function `preview_csv_data` to preview the CSV data if the task include CSV dataset or examples.
            - Generate the commands to run and test the current script, and the dependencies list required for this script.
            - You only write Python scripts, don't write Jupiter notebooks which require interactive execution.
            - Make sure the code has met the task description, and the suggested methods.
            - Make sure the output format and the output file path is correct.
            """

        self.search_prompt = """
        - Performing web searches use function `web_search` to get up-to-date information or additional context.
        """

        self.json_mode_prompt = """

        The output format should be in JSON format, include:
        
        1. The dependency list that the project needs to run.
        2. And the command to run and test the project.
        3. The reason why failed if the status is failed, put it in the "message" field.
        4. Whether the task requires execution and debug or not (it is "false" when create new directories or files).
         If the task requires modifying existing code or generating new code, it is "true". If the "command" is empty,
         the "debug" should be "false".
        
        Example JSON output:
        
        {
           "dependency":[
              "torch",
              "scikit-learn"
           ],
           "command":"python /path/to/your/project.py",
           "message":"the project-related has been generated in the project.py.",
           "debug":"true"
        }
        
        """

        if single_file:
            self.json_mode_prompt = """
        
            The output format should be in JSON format, include:
            
            1. The dependency list that the project needs to run.
            2. And the command and the parameters to run and test the script.
            
            Example JSON output:
            
            {
               "dependency":[
                  "torch",
                  "scikit-learn"
               ],
               "command":"python /path/to/your/project.py",
            }
            
            """

        self.functions = [
            schema_read_file,
            schema_create_file,
            schema_write_file,
            schema_list_files,
            schema_create_directory,
            schema_preview_csv_data
        ]

        if config_data.get('search_key'):
            self.functions.append(schema_web_search)
            self.sys_prompt += self.search_prompt

        self.sys_prompt += self.json_mode_prompt
        self.chat_history.append({"role": 'system', "content": self.sys_prompt})

    def read_requirement(self, advisor_report: str):
        """
        Read the user requirement and the advisor report.
        :param advisor_report:
        :return:
        """
        req_details = f"""
        The overall project information:\n
        {advisor_report}
        """
        self.chat_history.append({"role": "system", "content": req_details})

    def code(self, task_dict: dict):
        """
        Handle the query from the model query response.
        Args:
            task_dict: the task dictionary.
        """
        task_prompt = textwrap.dedent(f"""
            You are required to complete task: {task_dict.get('task')}.\n
            Task description: {task_dict.get('description')}
            """)

        with self.console.status(f"Coder is working on the task: {task_dict.get('task')}..."):
            self.chat_history.append({"role": "user", "content": task_prompt})
            text = self.model.query(
                self.chat_history,
                function_call='auto',
                functions=self.functions,
                response_format={"type": "json_object"}
            )

            self.chat_history.append({"role": "assistant", "content": text})
            code_summary = json.loads(text)
            code_summary.update({'task': task_dict.get('task'), 'task_description': task_dict.get('description')})
        return code_summary

    def debug(self, task_dict: dict, debug_report: dict):
        """
        Handle the query from the model query response.
        :param task_dict: the task dictionary.
        :param debug_report: the debug report from DebugAgent.
        :return:
        """
        improve_prompt = textwrap.dedent(f"""
        You are required improve the existing project.\n
        The required changes: {debug_report.get("changes")}\n
        The suggestion: {debug_report.get("suggestion")}

        """)

        with self.console.status(f"Coder is improving the code for task {task_dict.get('task')}..."):
            self.chat_history.append({"role": "user", "content": improve_prompt})
            text = self.model.query(
                self.chat_history,
                function_call='auto',
                functions=self.functions,
                response_format={"type": "json_object"}
            )

            self.chat_history.append({"role": "assistant", "content": text})
            code_summary = json.loads(text)
            code_summary.update({'task': task_dict.get('task'), 'task_description': task_dict.get('description')})
        return code_summary

    def interact(self, task_dict: dict):
        """
        Interact with the user to code the task.
        Args:
            task_dict: the task dictionary.
        """
        self.code_summary = self.code(task_dict)
        print_in_box(process_summary(self.code_summary), self.console, title="MLE Developer", color="cyan")
        while True:
            suggestion = questionary.text(
                "Any feedback to MLE developer? (ENTER to move to the next stage, \"exit\" to exit the project)"
            ).ask()

            if not suggestion:
                break

            if suggestion.lower() in ["exit"]:
                sys.exit(0)

            with self.console.status(f"MLE Developer is working on the task: {task_dict.get('task')}..."):
                self.chat_history.append({"role": "user", "content": suggestion})
                text = self.model.query(
                    self.chat_history,
                    function_call='auto',
                    functions=self.functions,
                    response_format={"type": "json_object"}
                )

                self.chat_history.append({"role": "assistant", "content": text})
                self.code_summary = json.loads(text)
                self.code_summary.update(
                    {
                        'task': task_dict.get('task'),
                        'task_description': task_dict.get('description')
                    }
                )
            print_in_box(process_summary(self.code_summary), self.console, title="MLE Developer", color="cyan")
        return self.code_summary
