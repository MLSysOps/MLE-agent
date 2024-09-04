import os
import re
import yaml
import click
import pickle
import questionary
from pathlib import Path
from rich.live import Live
from rich.panel import Panel
from rich.console import Console
from rich.markdown import Markdown

import mle
from mle.model import load_model
from mle.agents import CodeAgent
import mle.workflow as workflow
from mle.utils import Memory
from mle.utils.system import get_config, write_config

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
@click.option('--model', default=None, help='The model to use for the chat.')
def start(mode, model):
    """
    start: start the chat with LLM.
    """
    if not check_config():
        return

    if mode == 'general':
        # Baseline mode
        return workflow.baseline(os.getcwd(), model)


@cli.command()
@click.pass_context
@click.argument('repo', required=False)
@click.option('--model', default=None, help='The model to use for the chat.')
def report(ctx, repo, model):
    """
    report: generate report with LLM.
    """
    if repo is None:
        # TODO: support local project report
        repo = questionary.text(
            "What is your GitHub repository? (e.g., MLSysOps/MLE-agent)"
        ).ask()

    if not re.match(r'.*/.*', repo):
        console.log("Invalid github repository, "
                    "Usage: 'mle report <organization/name>'")
        return False

    if not check_config():
        # build a new project for github report generating
        project_name = f"mle-report-{repo.replace('/', '_').lower()}"
        ctx.invoke(new, name=project_name)
        # enter the new project for report generation
        work_dir = os.path.join(os.getcwd(), project_name)
        os.chdir(work_dir)
        return workflow.report(work_dir, repo, model)

    return workflow.report(os.getcwd(), repo, model)


@cli.command()
def chat():
    """
    chat: start an interactive chat with LLM to work on your ML project.
    """
    if not check_config():
        return

    model = load_model(os.getcwd(), "gpt-4o")
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
        choices=['OpenAI', 'Ollama', 'Claude']
    ).ask()

    api_key = None
    if platform == 'OpenAI':
        api_key = questionary.password("What is your OpenAI API key?").ask()
        if not api_key:
            console.log("API key is required. Aborted.")
            return

    elif platform == 'Claude':
        api_key = questionary.password("What is your Anthropic API key?").ask()
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


@cli.command()
def integrate():
    """
    integrate: integrate the third-party extensions.
    """
    if not check_config():
        return

    config = get_config()
    if "integration" not in config.keys():
        config["integration"] = {}

    platform = questionary.select(
        "Which platform do you want to integrate?",
        choices=['GitHub', 'Google Calendar']
    ).ask()

    if platform == "GitHub":
        token = get_config().get("integration").get("github").get("token")
        if token:
            print("GitHub is already integrated.")
        else:
            token = questionary.password(
                "What is your GitHub token? (https://github.com/settings/tokens)"
            ).ask()

            config["integration"]["github"] = {
                "token": token,
            }
            write_config(config)

    elif platform == "Google Calendar":
        from mle.integration.google_calendar import google_calendar_login
        token = get_config().get("integration").get("google_calendar").get("token")
        if token:
            print("Google Calendar is already integrated.")
        else:
            token = google_calendar_login()
            config["integration"]["google_calendar"] = {
                "token": pickle.dumps(token, fix_imports=False),
            }
            write_config(config)
