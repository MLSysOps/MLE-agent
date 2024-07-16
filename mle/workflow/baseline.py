"""
Baseline Mode: the mode to quickly generate the AI baseline based on the user's requirements.
"""
import os
import textwrap
import questionary
from rich.console import Console
from mle.model import load_model
from mle.utils import print_in_box
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

    # advisor agent gives suggestions in a report
    advisor = AdviseAgent(model)
    report = advisor.interact(ask_data(dataset) + "\n\n" + "User Requirement: " + ml_requirement)
    print_in_box(report, console, title="MLE Advisor", color="green")

    # plan agent generates the coding plan
    planner = PlanAgent(model)
    coding_plan = planner.interact(report)

    # code agent codes the tasks
    coder = CodeAgent(model, work_dir)
    debugger = DebugAgent(model)

    for current_task in coding_plan.get('tasks'):
        with console.status(f"Coder is coding the tasks: {current_task.get('task')}"):
            task_requirement = textwrap.dedent(f"""
            You are required to complete task: {current_task.get('task')}.\n
            You should: {current_task.get('description')}
            """)

            code_report = coder.code(task_requirement)
            code_prompt = textwrap.dedent(f"""
            I have finish the task: {current_task.get('task')}. {code_report.get('message')}\n
            The dependencies required to run the code: {code_report.get('dependency')}\n
            The command to run the code: {code_report.get('command')}\n
            Whether the code is required to execute and debug: {code_report.get('debug')}
            """)
            print_in_box(code_prompt, console, title="MLE Developer", color="cyan")

        while True:
            is_debugging = code_report.get('debug')
            if is_debugging == 'true' or is_debugging == 'True':
                with console.status("Debugger is executing and debugging the code..."):
                    debug_report = debugger.analyze(code_prompt)

                if debug_report.get('status') == 'success':
                    print_in_box(f"debug with {debug_report.get('status')}", console, title="Debugger", color="yellow")
                    break
                else:
                    improve_prompt = textwrap.dedent(f"""
                    You are required improve the existing project.\n
                    The required changes: {debug_report.get("changes")}\n
                    The suggestion: {debug_report.get("suggestion")}
                    
                    """)
                    print_in_box(improve_prompt, console, title="MLE Debugger", color="yellow")
                    with console.status("Coder is improving the code..."):
                        code_report = coder.code(improve_prompt)
            else:
                break
