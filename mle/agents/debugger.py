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

    1. You need to first read the structure of the project, understand it. You need to use
     function `list_files` to show the whole project structure.
    2. Then you may need to call `read_file` function to read the content of the code file, check
     if there are any errors or bugs in the code by viewing it. Give some comments on the code based on
     the best practice, it comes from code style, code structure, or code logic, etc.
    3. You may need to call `execute_command` function to test a code locally, this command will return the
     logs from the program.
    4. You need to debug the code based on the logs, if there are errors or exceptions, you may need to
     call `web_search` function to search for the solutions or reasons for the errors.
    5. The final output is a QA report, which includes the comment on the code, the requested changes on
     specific file and lines, and the reasons for the changes. If there is any error, you need to provide
     the reason and the solution for it.
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
            functions=self.functions
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
                functions=self.functions
        ):
            if content:
                text += content
                yield text

        self.chat_history.append({"role": "assistant", "content": text})
