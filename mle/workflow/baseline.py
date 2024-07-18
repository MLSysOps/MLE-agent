"""
Baseline Mode: the mode to quickly generate the AI baseline based on the user's requirements.
"""
import os
import questionary
from rich.console import Console
from mle.model import load_model
from mle.utils import print_in_box, ask_text
from mle.agents import CodeAgent, DebugAgent, AdviseAgent, PlanAgent


def ask_data(data_str: str):
    """
    Ask the user to provide the data information.
    :param data_str: the input data string. Now, it should be the name of the public dataset or
     the path to the local CSV file.
    :return: the formated data information.
    """
    if os.path.isfile(data_str) and data_str.lower().endswith('.csv'):
        return f"CSV dataset location: {data_str}"
    else:
        return f"Dataset: {data_str}"


def baseline(work_dir: str, model='gpt-4o'):
    """
    The workflow of the baseline mode.
    :return:
    """

    console = Console()
    model = load_model(work_dir, model)

    # ask for the data information
    dataset = ask_text("Please provide dataset information (the public dataset name or a path to your local .csv file)")
    if not dataset:
        print_in_box("The dataset is empty. Aborted", console, title="Error", color="red")
        return

    # ask for the user requirement
    ml_requirement = ask_text("Please provide the user requirement")
    if not ml_requirement:
        print_in_box("The user's requirement is empty. Aborted", console, title="Error", color="red")
        return

    # advisor agent gives suggestions in a report
    advisor = AdviseAgent(model, console)
    advisor_report = advisor.interact("User requirement: " + ml_requirement + "\n" + ask_data(dataset))

    # plan agent generates the coding plan
    planner = PlanAgent(model, console)
    coding_plan = planner.interact(advisor_report)

    # code agent codes the tasks and debug with the debug agent
    coder = CodeAgent(model, work_dir, console)
    coder.read_requirement(advisor_report)
    debugger = DebugAgent(model, console)

    is_auto_mode = questionary.confirm(
        "The MLE developer is about to start the coding tasks. "
        "Do you want to debug the tasks automatically (If no, MLE agent will only focus on the coding tasks,"
        " and you have to run and debug the task code by yourself)?"
    ).ask()

    for current_task in coding_plan.get('tasks'):
        code_report = coder.interact(current_task)
        is_debugging = code_report.get('debug')

        if is_auto_mode:
            while True:
                if is_debugging == 'true' or is_debugging == 'True':
                    with console.status("Debugger is executing and debugging the code..."):
                        debug_report = debugger.analyze(code_report)
                    if debug_report.get('status') == 'success':
                        break
                    else:
                        code_report = coder.debug(current_task, debug_report)
                else:
                    break
