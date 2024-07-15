"""
Kaggle Mode: the mode to run the kaggle competition automatically.
"""
import os
import questionary
from rich.console import Console

from mle.model import load_model
from mle.utils import print_in_box
from mle.agents import AdviseAgent
from mle.function import preview_csv_data


def ask_data(data_str: str):
    if os.path.isfile(data_str) and data_str.lower().endswith('.csv'):
        return preview_csv_data(data_str)
    else:
        return f"Dataset: {data_str}"


def kaggle(work_dir: str, model='gpt-4o'):
    console = Console()
    model = load_model(work_dir, model)

    # ask for the data information
    dataset = questionary.text("Dataset (public dataset name or a path to local .csv file):").ask()
    if not dataset:
        print_in_box("The dataset is empty. Aborted", console, title="Error", color="red")
        return

    # ask for the user requirement
    ml_requirement = questionary.text("User requirement:").ask()
    if not ml_requirement:
        print_in_box("The user's requirement is empty. Aborted", console, title="Error", color="red")
        return

    print_in_box(ml_requirement, console, title="User")

    advisor = AdviseAgent(model)
    report = advisor.interact(ask_data(dataset) + "\n\n" + "User Requirement: " + ml_requirement)
    print_in_box(report, console, title="MLE Advisor", color="green")
