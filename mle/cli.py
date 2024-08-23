import os
import yaml
import click
import questionary
from pathlib import Path
from rich.live import Live
from rich.panel import Panel
from rich.console import Console
from rich.markdown import Markdown

import mle
from mle.utils import Memory
from mle.model import load_model
from mle.agents import CodeAgent
from mle.workflow import baseline, kaggle, report

console = Console()
CONFIG_FILE = 'project.yml'


def check_config():
    """
    check_config: check if the configuration file exists.
    :return: True if the configuration file exists, False otherwise.
    """""
    current_work_dir = os.getcwd()
    config_path = os.path.join(current_work_dir, CONFIG_FILE)

    if not os.path.exists(config_path):
        console.log("Configuration file not found. Please run 'mle new' first.")
        return False

    with open(config_path, 'r') as file:
        data = yaml.safe_load(file)
        if data.get('search_key'):
            os.environ["SEARCH_API_KEY"] = data.get('search_key')

    return True


@click.group()
@click.version_option(version=mle.__version__)
def cli():
    """
    MLE-Agent: The CLI tool to build machine learning projects.
    """
    pass


@cli.command()
@click.argument('mode', default='general')
@click.option('--model', default='gpt-4o', help='The model to use for the chat.')
def start(mode, model):
    """
    start: start the chat with LLM.
    """
    if not check_config():
        return

    if mode == 'kaggle':
        # Kaggle mode
        console.log("Kaggle mode is not supported yet. Aborted.")
        return kaggle(os.getcwd(), model)
    elif mode == 'report':
        # Report mode
        return report(os.getcwd(), model)
    else:
        # Baseline mode
        return baseline(os.getcwd(), model)


@cli.command()
def chat():
    """
    chat: start an interactive chat with LLM to work on your ML project.
    """
    if not check_config():
        return

    model = load_model(os.getcwd(), model_name='gpt-4o')
    coder = CodeAgent(model)

    while True:
        try:
            user_pmpt = questionary.text("[Exit/Ctrl+D]: ").ask()
            if user_pmpt:
                with Live(console=Console()) as live:
                    for text in coder.chat(user_pmpt.strip()):
                        live.update(
                            Panel(Markdown(text), title="[bold magenta]MLE-Agent[/]", border_style="magenta"),
                            refresh=True
                        )
        except (KeyboardInterrupt, EOFError):
            exit()


@cli.command()
@click.argument('name')
def new(name):
    """
    new: create a new machine learning project with the given NAME.
    """
    if not name:
        console.log("Please provide a valid project name. Aborted.")
        return

    platform = questionary.select(
        "Which language model platform do you want to use?",
        choices=['OpenAI', 'Ollama']
    ).ask()

    api_key = None
    if platform == 'OpenAI':
        api_key = questionary.password("What is your OpenAI API key?").ask()
        if not api_key:
            console.log("API key is required. Aborted.")
            return

    search_api_key = questionary.password("What is your Tavily API key? (if no, the web search will be disabled)").ask()
    if search_api_key:
        os.environ["SEARCH_API_KEY"] = search_api_key

    # make a directory for the project
    project_dir = os.path.join(os.getcwd(), name)
    Path(project_dir).mkdir(parents=True, exist_ok=True)
    with open(os.path.join(project_dir, CONFIG_FILE), 'w') as outfile:
        yaml.dump({
            'platform': platform,
            'api_key': api_key,
            'search_key': search_api_key
        }, outfile, default_flow_style=False)

    # init the memory
    Memory(project_dir)
