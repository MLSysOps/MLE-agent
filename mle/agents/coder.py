import sys
import json
from typing import Dict, Any, List
from rich.console import Console

from mle.function import *
from mle.utils import get_config
from mle.utils import print_in_box

def process_summary(summary_dict: Dict[str, Any]) -> str:
    return f"""
MLE Developer has finished the task: {summary_dict.get('task')}.\n
Task description: {summary_dict.get('task_description')}\n
{summary_dict.get('message')}\n
Dependencies you are required to run the code: {summary_dict.get('dependency')}\n
Command to run the code: {summary_dict.get('command')}\n
Whether the code is required to execute and debug: {summary_dict.get('debug')}"""

class CodeAgent:
    def __init__(self, model, working_dir: str = '.', console: Console = None):
        config_data = get_config()
        self.code_summary: Dict[str, Any] = {}
        self.model = model
        self.chat_history: List[Dict[str, str]] = []
        self.working_dir = working_dir
        self.console = console or Console()

        self.sys_prompt = self._generate_system_prompt(config_data)
        self.chat_history.append({"role": 'system', "content": self.sys_prompt})

    def _generate_system_prompt(self, config_data: Dict[str, Any]) -> str:
        prompt = f"""
        You are a programmer working on an Machine Learning task using Python.
        You are currently working on: {self.working_dir}.
        
        Your capabilities include:
        
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
        
        if config_data.get('search_key'):
            prompt += """
            9. Performing web searches use function `web_search` to get up-to-date information or additional context.
            """

        prompt += """
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
        return prompt

    def read_requirement(self, advisor_report: str) -> None:
        req_details = f"""
        The overall project information:\n
        {advisor_report}
        """
        self.chat_history.append({"role": "system", "content": req_details})

    def code(self, task_dict: Dict[str, str]) -> Dict[str, Any]:
        task_prompt = f"""
            You are required to complete task: {task_dict.get('task')}.\n
            You should: {task_dict.get('description')}
            """

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

    def debug(self, task_dict: Dict[str, str], debug_report: Dict[str, Any]) -> Dict[str, Any]:
        improve_prompt = f"""
        You are required improve the existing project.\n
        The required changes: {debug_report.get("changes")}\n
        The suggestion: {debug_report.get("suggestion")}
        """

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

    def interact(self, task_dict: Dict[str, str]) -> Dict[str, Any]:
        self.code_summary = self.code(task_dict)
        print_in_box(process_summary(self.code_summary), self.console, title="MLE Developer", color="cyan")
        while True:
            suggestion = questionary.text(
                "Any feedback to MLE developer? (ENTER to move to the next stage, \"exit\" to exit the project)"
            ).ask()

            if not suggestion:
                break

            if suggestion.lower() == "exit":
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

    def chat(self, user_prompt: str) -> str:
        text = ''
        self.chat_history.append({"role": "user", "content": user_prompt})
        for content in self.model.stream(
                self.chat_history,
                function_call='auto',
                functions=[
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
        ):
            if content:
                text += content
                yield text

        self.chat_history.append({"role": "assistant", "content": text})
