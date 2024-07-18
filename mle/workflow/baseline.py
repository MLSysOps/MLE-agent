"""
Baseline Mode: the mode to quickly generate the AI baseline based on the user's requirements.
"""
import os
from rich.console import Console
from mle.model import load_model
from mle.utils import print_in_box, ask_text
from mle.function import preview_csv_data
from mle.agents import CodeAgent, DebugAgent, AdviseAgent, PlanAgent


def ask_data(data_str: str):
    """
    Ask the user to provide the data information.
    :param data_str: the input data string. Now, it should be the name of the public dataset or
     the path to the local CSV file.
    :return: the formated data information.
    """
    if os.path.isfile(data_str) and data_str.lower().endswith('.csv'):
        return preview_csv_data(data_str)
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
    print_in_box(ml_requirement, console, title="User")

    # advisor agent gives suggestions in a report
    advisor = AdviseAgent(model, console)
    report = advisor.interact(ask_data(dataset) + "\n\n" + "User Requirement: " + ml_requirement)
    print_in_box(report, console, title="MLE Advisor", color="green")

    # plan agent generates the coding plan
    planner = PlanAgent(model, console)
    coding_plan = planner.interact(report)

    # code agent codes the tasks and debug with the debug agent
    # coder = CodeAgent(model, work_dir, console)
    # debugger = DebugAgent(model, console)
    #
    # is_manual_mode = questionary.confirm(
    #     "The MLE developer is about to start the coding tasks. "
    #     "Do you want to debug the tasks by yourself (If no, MLE agent will execute and debug the code automatically)"
    # ).ask()

    # for current_task in coding_plan.get('tasks'):
    #     code_report = coder.interact(current_task)
    #     is_debugging = code_report.get('debug')
    #
    #     # debug the code with two different modes
    #     if is_debugging == 'true' or is_debugging == 'True':
    #         if is_manual_mode:
    #             while True:
    #                 is_task_successful = questionary.confirm("Is the code execution successful?").ask()
    #                 if not is_task_successful:
    #                     error_message = questionary.text("Please provide the error message:").ask()
    #                     if error_message:
    #                         code_report.update({'error_message': error_message})
    #
    #                     debugger.analyze(code_report)
    #                     is_code_debug = questionary.confirm(
    #                         "Do you want MLE developer to improve the task? (if no, we will move to the next task)"
    #                     ).ask()
    #                     if not is_code_debug:
    #                         break
    #                     else:
    #                         code_report = coder.debug(current_task, code_report)
    #                 else:
    #                     break
    #         else:
    #             while True:
    #                 with console.status("Debugger is executing and debugging the code..."):
    #                     debug_report = debugger.analyze(code_report)
    #                 if debug_report.get('status') == 'success':
    #                     break
    #                 else:
    #                     code_report = coder.debug(current_task, debug_report)
