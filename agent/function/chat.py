import os

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel

from agent.types.const import CONFIG_CHAT_HISTORY_FILE
from agent.utils import Config
from agent.utils import list_all_files

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

    def handle_response(self, prompt):
        """
        Handle the response from the chat.
        :param prompt: the user prompt.
        :return:
        """
        text = ''
        self.chat_history.append({"role": "user", "content": prompt})
        response = self.agent.query(self.chat_history)

        for content in response:
            if content:
                text += content
                yield text

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
                for text in self.handle_response(prompt):
                    live.update(
                        Panel(Markdown(text), title="[bold magenta]MLE-Agent[/]", border_style="magenta"),
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
