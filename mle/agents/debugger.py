import json

from mle.function import *
from mle.utils import get_config, print_in_box

from rich.console import Console


def process_debug_report(debug_report):
    """
    Process the debug report.
    Args:
        debug_report: the debug report.
    """
    if debug_report.get("status") == "success":
        return "The code runs without errors."
    else:
        changes = debug_report.get("changes")
        suggestion = debug_report.get("suggestion")
        report_str = "The code is running with errors.\nChanges are required:\n"
        for change in changes:
            report_str += f"File: {change.get('file')}, Line: {change.get('line')}, Issue: {change.get('issue')}, " \
                          f"Suggestion: {change.get('suggestion')}\n"
        report_str += f"Overall Suggestion: {suggestion}"
        return report_str


class DebugAgent:

    def __init__(self, model, console=None, analyze_only=False):
        """
        DebugAgent: the agent to run the generated the code and then debug it. The return of the
        agent is an instruction to the user to modify the code based on the logs and web search.

        Args:
            model: the model to use.
            console: the console to use.
            analyze_only: if only analyze the code without execution
        """
        config_data = get_config()
        self.console = console
        if not self.console:
            self.console = Console()
        self.model = model
        self.chat_history = []
        self.sys_prompt = """
        You are a program error debugger working on a Python project.

        Your can leverage your capabilities by using the specific functions listed below:

        - Install the code dependencies using function `execute_command` based on the Developer's dependencies list.
        - Execute the code using function `execute_command` to test the code based on the Developer's instructions.
        - If the program returns errors, you need to debug the code based on the logs, you may need to first read the
         structure of the project using function `list_files`.
        - Then you may need to call `read_file` function to read the content of the code files, locate the error line
         and the reasons.
        - You don't need to care about the best practices and code styles, you only care about the errors in the code.

        """

        self.search_prompt = """
        - You need to debug the code based on the error logs, you may need to call `web_search` function to search for
         the solutions or reasons for the errors if needed.
        """

        self.json_mode_prompt = """
        
        Example JSON output if a program runs without errors:
        {
           "status":"success",
           "changes":[],
           "suggestion":""
        }
        
        Example JSON output if a program returns errors:
        {
           "status":"error",
           "changes":[
              {
                 "file":"xxx.py",
                 "line":10,
                 "issue":"xxx",
                 "suggestion":"xxx"
              },
            "suggestion":"Failed to find the target file. Please check the file path."
           ]
        }
        """

        self.functions = [
            schema_read_file,
            schema_list_files,
            schema_execute_command
        ]

        if analyze_only:
            self.sys_prompt = """
            You are a program error debugger working on a Python project. You target is to
             analyze the running logs and the source code to locate the errors. And give the
             suggestions to the developer to fix the errors.

            Your can leverage your capabilities by using the specific functions listed below:

            - Read and understand the running logs and the error messages.
            - Read the content of the source code files using function `read_file`, to locate the error line.
            - Give the suggestions to the developer to fix the errors.
            - Install missing dependencies using function `execute_command` based on the error logs.
            - If there is no error based on the exit code, you don't need to do anything but return the success status.
            """

        if config_data.get('search_key'):
            self.functions.append(schema_web_search)
            self.sys_prompt += self.search_prompt

        self.sys_prompt += self.json_mode_prompt
        self.chat_history.append({"role": 'system', "content": self.sys_prompt})

    def analyze_with_log(self, commands, logs):
        """
        Analyze the logs.
        :param commands: the commands to execute.
        :param logs: the logs to analyze.
        :return:
        """
        analyze_prompt = f"""
        The command to execute the code: {commands} \n
        The logs to analyze: {logs} \n
        """

        self.chat_history.append({"role": "user", "content": analyze_prompt})
        try:
            text = self.model.query(
                self.chat_history,
                function_call='auto',
                functions=self.functions,
                response_format={"type": "json_object"}
            )
        except Exception as e:
            print(f"Error occurred while querying the model: {e}")
            return {}

        self.chat_history.append({"role": "assistant", "content": text})
        report_dict = json.loads(text)
        print_in_box(process_debug_report(report_dict), self.console, title="MLE Debugger", color="yellow")
        return report_dict

    def analyze(self, code_report):
        """
        Handle the query from the model query response.
        Args:
            code_report: the code report from the MLE developer.
        """
        debug_prompt = f"""
        Please help me debug the current task: {code_report.get('task')}. {code_report.get('messages')}\n
        The task description: {code_report.get('task_description')}
        The dependencies required for this task: {code_report.get('dependencies')}
        The command to execute the code: {code_report.get('command')}
        
        """

        error_msg = code_report.get('error_message')
        if error_msg:
            debug_prompt += f"Error message: {error_msg}\n"

        self.chat_history.append({"role": "user", "content": debug_prompt})
        try:
            text = self.model.query(
                self.chat_history,
                function_call='auto',
                functions=self.functions,
                response_format={"type": "json_object"}
            )
        except Exception as e:
            print(f"Error occurred while querying the model: {e}")
            return {}

        self.chat_history.append({"role": "assistant", "content": text})
        report_dict = json.loads(text)
        print_in_box(process_debug_report(report_dict), self.console, title="MLE Debugger", color="yellow")
        return report_dict
