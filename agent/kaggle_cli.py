import os

import click
import questionary

from agent.cli import build_config
from agent.integration.kaggle_workflow import KaggleAgent
from agent.types import Project
from agent.utils import Console, Config, read_project_state, create_project, load_model

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
    if configuration.read() is None:
        console.log("Configuration file does not exist. Creating a new one...")
        build_config()

    if configuration.read().get('project') is None:
        console.log("You have not set up a project yet.")
        console.log("Please create a new project first using 'mle kaggle new your_project_name' command,"
                    " or set the project using 'mle project switch'.")
        return

    p = read_project_state(configuration.read()['project']['name'])
    if p is None:
        console.log("Could not find the project in the database. Aborted.")
        return

    if reset:
        console.log("Resetting the project state.")
        p = Project(
            name=p.name,
            description=p.description,
            lang=p.lang,
            llm=p.llm,
            path=p.path,
            kaggle_config=p.kaggle_config,
            kaggle_competition=p.kaggle_competition
        )

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
