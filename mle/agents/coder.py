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
        2. Writing clean, efficient, and well-documented code using function `create_file`
        3. Exam the source code make re-use the existing code snippets using function `read_file`, or
         modify the code to meet the requirements using function `write_file`
        4. Offering architectural insights and design patterns
        5. Listing files in the  project to understand the project structure with function `list_files`
        6. Reading and analyzing existing files in the project directory using function `read_file`
        7. Set clear, achievable goals for yourself based on the user's requirements and task descriptions
        
        """
        self.search_prompt = """
        
        8. Performing web searches use function `web_search` to get up-to-date information or additional context
        """
        self.json_mode_prompt = """

        The output format should be in JSON format, include:
        
        1. the coding status (completed or failed)
        2. the dependency list that the project needs to run
        3. and the command to run and test the project
        4. the reason why failed if the status is failed
        
        Two examples of JSON output:
        
        {
           "status":"completed",
           "dependency":[
              "torch",
              "scikit-learn"
           ],
           "command":"python /path/to/your/project.py",
           "reason":""
        }
            
        {
           "status":"failed",
           "dependency":[
              "torch",
              "scikit-learn"
           ],
           "command":"python /path/to/your/project.py",
           "reason":"error messages"
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

    def code(self, user_prompt):
        """
        Handle the query from the model query response.
        Args:
            user_prompt: the user prompt.
        """
        self.chat_history.append({"role": 'system', "content": self.sys_prompt})
        self.chat_history.append({"role": "user", "content": user_prompt})
        text = self.model.query(
            self.chat_history,
            function_call='auto',
            functions=self.functions,
            response_format={"type": "json_object"}
        )

        self.chat_history.append({"role": "assistant", "content": text})
        return text

    def improve(self, debug_result: str):
        """
        Improve the code based on the debug result from DebugAgent.
        :return:
        """
        pass

    def chat(self, user_prompt):
        """
        Handle the response from the model streaming.
        The stream mode is integrative with the model streaming function, we don't
        need to set it into the JSON mode.
        Args:
            user_prompt: the user prompt.
        """
        text = ''
        self.chat_history.append({"role": 'system', "content": self.sys_prompt})
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