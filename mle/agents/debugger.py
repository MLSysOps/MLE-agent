from mle.function import *
from mle.utils import get_config


class DebugAgent:

    def __init__(self, model):
        """
        DebugAgent: the agent to run the generated the code and then debug it. The return of the
        agent is an instruction to the user to modify the code based on the logs and web search.

        Args:
            model: the model to use.
        """
        config_data = get_config()
        self.model = model
        self.chat_history = []
        self.sys_prompt = """
        You are a program error debugger working on a Python project. Your capabilities include:

        1. Install the code dependencies using function `execute_command` based on the Developer's dependencies list
        2. Execute the code using function `execute_command` to test the code based on the Developer's instruction
        3. If the program returns errors, you need to debug the code based on the logs, you may need to first read the
         structure of the project using function `list_files`.
        4. Then you may need to call `read_file` function to read the content of the code files, locate the error line
         and the reasons.
        5. You don't need to care about the best practices and code styles, you only care about the errors in the code.

        """
        self.search_prompt = """
        
        7. You need to debug the code based on the error logs, you may need to call `web_search` function to search for
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

        if config_data.get('search_key'):
            self.functions.append(schema_web_search)
            self.sys_prompt += self.search_prompt

        self.sys_prompt += self.json_mode_prompt
        self.chat_history.append({"role": 'system', "content": self.sys_prompt})

    def handle_query(self, user_prompt):
        """
        Handle the query from the model query response.
        Args:
            user_prompt: the user prompt.
        """
        self.chat_history.append({"role": "user", "content": "Developer: " + user_prompt})
        text = self.model.query(
            self.chat_history,
            function_call='auto',
            functions=self.functions,
            response_format={"type": "json_object"}
        )

        self.chat_history.append({"role": "assistant", "content": text})
        return text
