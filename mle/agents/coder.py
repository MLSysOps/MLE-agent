import json
from mle.function import *
from mle.utils import get_config


class CodeAgent:

    def __init__(self, model, working_dir='.'):
        """
        CodeAgent: the agent to solve the given coding problems, by planning coding tasks, searching websites,
        and generating code snippets. It does not execute the code, only make use of built-in functions to provides
         the code snippets to solve the problem.

        Args:
            model: the model to use.
        """
        config_data = get_config()
        self.model = model
        self.chat_history = []
        self.working_dir = working_dir
        self.sys_prompt = f"""
        You are a programmer working on a Python project. You are currently working on: {self.working_dir}.
        
        Your capabilities include:
        
        1. Creating project structures based on the user requirement using function `create_directory`
        2. Writing clean, efficient, and well-documented code using function `create_file` and `write_file`
        3. Listing files in the  project to understand the project structure with function `list_files`
        4. Exam the source code make re-use the existing code snippets using function `read_file`, or
            modify the code to meet the requirements using the function `write_file`
        5. Writing the code into the file when creating new files, do not create empty files
        7. For the ML training and serving scripts, you should write log/print functions to give feedback to the user
        8. Decide whether the task requires execution and debugging before moving to the next or not
        """
        self.search_prompt = """
        9. Performing web searches use function `web_search` to get up-to-date information or additional context
        """
        self.json_mode_prompt = """

        The output format should be in JSON format, include:
        
        1. the coding status (completed or failed)
        2. the dependency list that the project needs to run
        3. and the command to run and test the project
        4. the reason why failed if the status is failed, put it in the "message" field
        5. whether the task requires debugging or not -- If the task only create new directories or files, it is "false"
        . If the task requires modifying existing code or generating new code, it is "true". If the "command" is empty,
         the "debug" should be "false".
        
        Two examples of JSON output:
        
        {
           "status":"completed",
           "dependency":[
              "torch",
              "scikit-learn"
           ],
           "command":"python /path/to/your/project.py",
           "message":"the project-related has been generated in the project.py.",
           "debug":"true"
        }
            
        {
           "status":"failed",
           "dependency":[],
           "command":"",
           "message":"error messages",
           "debug":"false"
        }
        
        """
        self.functions = [
            schema_read_file,
            schema_create_file,
            schema_write_file,
            schema_list_files,
            schema_create_directory
        ]

        if config_data.get('search_key'):
            self.functions.append(schema_web_search)
            self.sys_prompt += self.search_prompt

        self.sys_prompt += self.json_mode_prompt
        self.chat_history.append({"role": 'system', "content": self.sys_prompt})

    def code(self, user_prompt):
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
        return json.loads(text)

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
                functions=self.functions
        ):
            if content:
                text += content
                yield text

        self.chat_history.append({"role": "assistant", "content": text})
