from mle.function import *


class CodeAgent:

    def __init__(self, model):
        """
        CodeAgent: the agent to solve the given coding problems, by planning coding tasks, searching websites,
        and generating code snippets. It does not execute the code, only make use of built-in functions to provides
         the code snippets to solve the problem.

        Args:
            model: the model to use.
        """
        self.model = model
        self.chat_history = []
        self.sys_prompt = """
    You are a programmer working on a Python project. Your capabilities include:
    
    1. Creating project structures, including folders and files
    2. Writing clean, efficient, and well-documented code
    3. Offering architectural insights and design patterns
    4. Staying up-to-date with the latest technologies and industry trends
    5. Reading and analyzing existing files in the project directory
    6. Listing files in the root directory of the project
    7. Set clear, achievable goals for yourself based on the user's request
    8. When you use search make sure you use the best query to get the most accurate and up-to-date information
    9. Performing web searches to get up-to-date information or additional context
    10. You should work under the given project directory
    
    When asked to create a project:
    - Always start by creating a root folder for the project.
    - Then, create the necessary subdirectories and files within that root folder.
    - Organize the project structure logically and follow best practices for the specific type of project being created.
    - Use the provided tools to create folders and files as needed.
    
    When asked to make edits or improvements:
    - Use the read_file tool to examine the contents of existing files.
    - Analyze the code and suggest improvements or make necessary edits.
    - Use the write_to_file tool to implement changes.

    When you need current information or feel that a search could provide a better answer, use the web_search tool.
     This tool performs a web search and returns a concise answer along with relevant sources.
    
    """
        self.functions = [
            schema_read_file,
            schema_create_file,
            schema_write_file,
            schema_list_files,
            schema_create_directory,
            schema_web_search
        ]
        self.chat_history.append({"role": 'system', "content": self.sys_prompt})

    def handle_query(self, user_prompt, work_dir: str = None):
        """
        Handle the query from the model query response.
        Args:
            user_prompt: the user prompt.
            work_dir: the working directory.
        """
        self.chat_history.append({"role": "user", "content": user_prompt + f"\nproject directory: {work_dir}"})
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
