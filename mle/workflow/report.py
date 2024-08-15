"""
Baseline Mode: the mode to quickly generate the AI baseline based on the user's requirements.
"""
import os
import questionary
from rich.console import Console
from mle.model import load_model
from mle.utils import print_in_box, ask_text, WorkflowCache
from mle.agents import AdviseAgent


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


def report(work_dir: str, model='gpt-4o'):
    """
    The workflow of the baseline mode.
    :return:
    """

    console = Console()
    cache = WorkflowCache(work_dir)
    model = load_model(work_dir, model)

    if not cache.is_empty():
        step = ask_text(
            f"MLE has already pass through the following steps: \n{cache}\n Pick a step for resume (ENTER to continue the workflow)")
        if step:
            step = int(step)
            for i in range(step, cache.current_step() + 1):
                cache.remove(i)  # remove the stale step caches

    # ask for the data information
    with cache(step=1, name="ask for the data information") as ca:
        dataset = ca.resume("dataset")
        if dataset is None:
            dataset = ask_text("Please provide your dataset information (a public dataset name or a local file path)")
            if not dataset:
                print_in_box("The dataset is empty. Aborted", console, title="Error", color="red")
                return
            ca.store("dataset", dataset)

    # ask for the user requirement
    with cache(step=2, name="ask for the user requirement") as ca:
        ml_requirement = ca.resume("ml_requirement")
        if ml_requirement is None:
            ml_requirement = ask_text("Please provide the user requirement")
            if not ml_requirement:
                print_in_box("The user's requirement is empty. Aborted", console, title="Error", color="red")
                return
        ca.store("ml_requirement", ml_requirement)

    # advisor agent gives suggestions in a report
    with cache(step=3, name="advisor agent gives suggestions in a report") as ca:
        advisor_report = ca.resume("advisor_report")
        if advisor_report is None:
            advisor = AdviseAgent(model, console)
            advisor_report = advisor.interact(
                "[green]User Requirement:[/green] " + ml_requirement + "\n" + ask_data(dataset))
        ca.store("advisor_report", advisor_report)
