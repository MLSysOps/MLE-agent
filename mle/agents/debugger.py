from mle.function import *


class DebugAgent:

    def __init__(self, model):
        """
        DebugAgent: the agent to run the generated the code and then debug it. The return of the
        agent is an instruction to the user to modify the code based on the logs and web search.

        Args:
            model: the model to use.
        """
        self.model = model
        self.chat_history = []
        self.sys_prompt = """
    You are a program tester working on a Python project. Your capabilities include:

    1. You need to first call function `execute_command` function to test a code locally, this command will return the
     logs from the program.
    2. If the program returns no errors, then you should return a report with JSON format:
     {{"execution": "no errors", "changes": "none"}}.
    3. If the program returns errors, you need to debug the code based on the logs, you may need to first read the
     structure of the project, understand it. You need to use function `list_files` to show the whole project structure.
    4. Then you may need to call `read_file` function to read the content of the code file, check
     if there are any errors or bugs in the code by viewing it. Give some comments on the code based on
     the best practice, it comes from code style, code structure, or code logic, etc.
    5. You need to debug the code based on the logs, if there are errors or exceptions, you may need to
     call `web_search` function to search for the solutions or reasons for the errors.
    6. The final output if there is a bug should be a JSON object like this:
     {{"execution": "errors", "changes": [{"file": "xxx.py", "line": 10, "issue": "xxx", "suggestion": "xxx"}]}}
    7. All the return should be in JSON format.
     
    The target project path will given by the user:
    
    {{target project absolute path}}
    """
        self.functions = [
            schema_read_file,
            schema_list_files,
            schema_web_search,
            schema_execute_command
        ]
        self.chat_history.append({"role": 'system', "content": self.sys_prompt})

    def handle_query(self, user_prompt):
        """
        Handle the query from the model query response.
        Args:
            user_prompt: the user prompt.
        """
        self.chat_history.append({"role": "user", "content": user_prompt})
        text = self.model.query(
            self.chat_history,
            function_call='auto',
            functions=self.functions,
            response_format={"type": "json_object"}
        )

        self.chat_history.append({"role": "assistant", "content": text})
        return text

    def handle_stream(self, user_prompt):
        """
        Handle the response from the model streaming.
        Args:
            user_prompt: the user prompt.
        """
        text = ''
        self.chat_history.append({"role": "user", "content": user_prompt})
        for content in self.model.stream(
                self.chat_history,
                function_call='auto',
                functions=self.functions,
                response_format={"type": "json_object"}
        ):
            if content:
                text += content
                yield text

        self.chat_history.append({"role": "assistant", "content": text})
