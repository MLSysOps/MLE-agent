import os
from rich.live import Live
from rich.panel import Panel
from rich.console import Console
from rich.markdown import Markdown

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

from agent.const import CONFIG_CHAT_HISTORY_FILE
from agent.utils import Config, CONFIG_HOME
from agent.utils import extract_and_save_file, list_all_files

config = Config()
HISTORY_PATH = str(os.path.join(CONFIG_HOME, CONFIG_CHAT_HISTORY_FILE))


class Chat:
    def __init__(self, llm_agent):
        """
        Initialize the chat class.
        :param llm_agent: the language model agent.
        """
        self.agent = llm_agent
        self.chat_history = []
        self.console = Console()
        self.session = PromptSession(history=FileHistory(HISTORY_PATH))

    def add(self, role: str, content: str):
        """
        Add the chat to the history.
        :param role: the role.
        :param content: the content.
        :return: the chat history.
        """
        self.chat_history.append({"role": role, "content": content})
        return self.chat_history

    def chat_generator(self, message: str):
        """
        Generate the chat.
        :param message: the user message.
        :return:
        """
        self.chat_history.append({"role": "user", "content": message})

        try:
            response = self.agent.completions(self.chat_history)
            for chunk in response:
                if chunk:
                    yield chunk
        except Exception as e:
            raise Exception(f"GeneratorError: {e}")

    def handle_streaming(self, prompt):
        """
        Handle the streaming of the chat.
        :param prompt: the user prompt.
        :return:
        """
        text = ""
        block = "█ "
        with Live(console=self.console) as live:
            for token in self.chat_generator(prompt):
                content = token.choices[0].delta.content
                if content:
                    text = text + content
                if token.choices[0].finish_reason is not None:
                    block = ""
                markdown = Markdown(text + block)
                live.update(
                    Panel(markdown, title="[bold magenta]MLE Assistant[/]", border_style="magenta"),
                    refresh=True
                )

        saved_file, _ = extract_and_save_file(text)
        saved_info = f"Generated code saved as: {saved_file}"
        self.console.log(saved_info)
        self.chat_history.append({"role": "assistant", "content": text})

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
                    \n
                    The files under the project directory is: {list_all_files(config.read()['project']['path'])}
                """)
                self.handle_streaming(user_pmpt)
            except (KeyboardInterrupt, EOFError):
                exit()
