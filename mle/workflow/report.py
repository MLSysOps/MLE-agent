"""
Report Mode: the mode to generate the AI report based on the user's requirements.
"""
import os
import json
import questionary
from rich.console import Console
from mle.model import load_model
from mle.agents import SummaryAgent
from mle.utils import print_in_box
from mle.utils.system import get_config, write_config


def ask_data(data_str: str):
    """
    Ask the user to provide the data information.
    :param data_str: the input data string. Now, it should be the name of the public dataset or
     the path to the local CSV file.
    :return: the formated data information.
    """
    if os.path.isfile(data_str) and data_str.lower().endswith('.csv'):
        return f"[green]CSV Dataset Location:[/green] {data_str}"
    else:
        return f"[green]Dataset:[/green] {data_str}"


def ask_github_token():
    """
    Ask the user to integrate github.
    :return: the github token.
    """
    config = get_config() or {}
    if "integration" not in config.keys():
        config["integration"] = {}

    if "github" not in config["integration"].keys():
        token = questionary.password(
            "What is your GitHub token? (https://github.com/settings/tokens)"
        ).ask()

        config["integration"]["github"] = {"token": token}
        write_config(config)

    return config["integration"]["github"]["token"]


def report(work_dir: str, github_repo: str, model=None):
    """
    The workflow of the baseline mode.
    :return:
    """
    console = Console()
    model = load_model(work_dir, model)

    summarizer = SummaryAgent(model, github_repo=github_repo, github_token=ask_github_token())
    github_summary = summarizer.summarize()
    print_in_box(json.dumps(github_summary), console, title="Github Summarizer", color="green")
