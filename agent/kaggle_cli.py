import os

import click
import questionary

from agent.integration.kaggle_workflow import KaggleAgent
from agent.types import Project
from agent.utils import Console, Config, create_project, load_model
from .build_config import get_project_config

console = Console()
configuration = Config()


@click.group()
def kaggle():
    """
    kaggle: group of commands related to Kaggle project management.
    """
    pass


@kaggle.command()
@click.argument('name')
def new(name):
    """
    new: create a new Kaggle machine learning project with the given NAME.
    """
    if not name:
        console.log("Please provide a valid [red]kaggle [/red] project name. Aborted.")
        return

    kaggle_username = questionary.text("What is your Kaggle username?").ask()
    kaggle_key = questionary.text("What is your Kaggle API key?").ask()
    if not kaggle_username or not kaggle_key:
        console.log("Kaggle credentials are required for a Kaggle project. Aborted.")
        return

    kaggle_config = {
        "username": kaggle_username,
        "key": kaggle_key
    }

    description = questionary.text("What is the description of this project? (Optional)").ask()
    create_project(
        Project(
            name=name,
            description=description,
            lang=configuration.read()['general']['code_language'],
            llm=configuration.read()['general']['platform'],
            exp_track=configuration.read()['general']['experiment_tracking_tool'],
            kaggle_config=kaggle_config,
        ),
        set_current=True
    )


@kaggle.command()
@click.option('--reset', '-r', is_flag=True, help="Reset the Kaggle project state.")
def start(reset=False):
    """
    start: start the Kaggle project.
    """
    p = get_project_config(reset)

    if os.path.exists(p.path):
        if p.kaggle_config:
            console.log("Starting a Kaggle project...")
            kaggle_agent = KaggleAgent(p, load_model())
            kaggle_agent.invoke()
        else:
            console.log("This is not a Kaggle project. Aborted.")
    else:
        console.log(f"Project path '{p.path}' does not exist. Aborted.")


if __name__ == "__main__":
    kaggle()
