import os
import json
from rich.live import Live
from rich.panel import Panel
from rich.console import Console
from rich.markdown import Markdown

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

from agent.utils import Config
from agent.utils import extract_and_save_file, list_all_files
from agent.integration import get_function
from agent.const import CONFIG_CHAT_HISTORY_FILE

config = Config()


class Chat:
    def __init__(self, llm_agent):
        """
        Initialize the chat class.
        :param llm_agent: the language model agent.
        """
        self.agent = llm_agent
        self.chat_history = []
        self.console = Console()
        self.project_home = config.read().get('project')['path']
        self.session = PromptSession(
            history=FileHistory(str(os.path.join(self.project_home, CONFIG_CHAT_HISTORY_FILE)))
        )

    def add(self, role: str, content: str):
        """
        Add the chat to the history.
        :param role: the role.
        :param content: the content.
        :return: the chat history.
        """
        self.chat_history.append({"role": role, "content": content})
        return self.chat_history

    def handle_function_call(self, name, arguments):
        """
        Handle the function call.
        :param name: the function name.
        :param arguments: the function arguments.
        :return:
        """
        self.chat_history.append(
            {
                "role": "assistant",
                "content": "",
                "function_call": {"name": name, "arguments": arguments},
            }
        )

        if arguments != "":
            dict_args = json.loads(arguments)
            joined_args = ", ".join(f'{k}="{v}"' for k, v in dict_args.items())
        else:
            dict_args = {}
            joined_args = ""
        self.console.log(f"> @FunctionCall `{name}({joined_args})` \n\n")

        results = get_function(name).execute(**dict_args)
        self.chat_history.append({"role": "function", "content": results, "name": name})

        return results

    def handle_response(self, prompt):
        """
        Handle the response from the chat.
        :param prompt: the user prompt.
        :return:
        """
        text = block = ""
        func_name = func_arguments = ""

        self.chat_history.append({"role": "user", "content": prompt})
        response = self.agent.completions(self.chat_history, True)

        for token in response:
            content = token.choices[0].delta.content
            if content:
                text = text + content

            function_call = token.choices[0].delta.function_call
            if function_call:
                if function_call.name:
                    func_name = function_call.name
                if function_call.arguments:
                    func_arguments += function_call.arguments

            stop_reason = token.choices[0].finish_reason
            if stop_reason == "function_call":
                self.handle_function_call(func_name, func_arguments)
                yield from self.handle_response(prompt)
            if stop_reason == "stop":
                saved_file, _ = extract_and_save_file(text)
                saved_info = f"Generated code saved as: {saved_file}"
                block = f"\n{saved_info}"

            if text:
                yield Markdown(text + block)

        self.chat_history.append({"role": "assistant", "content": text})

    def handle_streaming(self, prompt, display=True):
        """
        Handle the streaming of the chat.
        :param prompt: the user prompt.
        :param display: the flag to display the chat.
        :return:
        """
        if display:
            with Live(console=self.console) as live:
                for markdown in self.handle_response(prompt):
                    live.update(
                        Panel(markdown, title="[bold magenta]MLE Assistant[/]", border_style="magenta"),
                        refresh=True
                    )
        else:
            self.handle_response(prompt)

    def start(self):
        """
        Start the chat.
        :return: None
        """
        while True:
            try:
                user_pmpt = self.session.prompt("[type to ask]: ").strip()
                # update the local file structure
                self.add("user", f"""
                    The files under the project directory is: {list_all_files(config.read()['project']['path'])}
                """)
                self.handle_streaming(user_pmpt)
            except (KeyboardInterrupt, EOFError):
                exit()
