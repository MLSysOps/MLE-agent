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
    cache = WorkflowCache(work_dir, 'chat')
    model = load_model(work_dir, model)
    chatbot = ChatAgent(model)

    if not cache.is_empty():
        if questionary.confirm(f"Would you like to continue the previous conversation?\n").ask():
            chatbot.chat_history = cache.resume_variable("conversation")

    with cache(step=1, name="chat") as ca:
        greets = chatbot.greet()
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
                ca.store("conversation", chatbot.chat_history)
            except (KeyboardInterrupt, EOFError):
                break
