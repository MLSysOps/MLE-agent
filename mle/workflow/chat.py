"""
Chat Mode: the mode to have an interactive chat with LLM to work on ML project.
"""
import os
import questionary
from rich.live import Live
from rich.panel import Panel
from rich.console import Console
from rich.markdown import Markdown
from mle.model import load_model
from mle.utils import print_in_box, WorkflowCache
from mle.agents import ChatAgent


def chat(work_dir: str, model=None):
    console = Console()
    cache = WorkflowCache(work_dir)
    model = load_model(work_dir, model)

    chatbot = ChatAgent(model)
    greets = chatbot.greet()
    if greets is not None:
        print_in_box(greets, console=console, title="MLE Chatbot", color="magenta")

    while True:
        try:
            user_pmpt = questionary.text("[Exit/Ctrl+D]: ").ask()
            if user_pmpt:
                with Live(console=Console()) as live:
                    for text in chatbot.chat(user_pmpt.strip()):
                        live.update(
                            Panel(Markdown(text), title="[bold magenta]MLE-Agent[/]", border_style="magenta"),
                            refresh=True
                        )
        except (KeyboardInterrupt, EOFError):
            exit()
