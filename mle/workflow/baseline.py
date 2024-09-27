"""
Baseline Mode: the mode to quickly generate the AI baseline based on the user's requirements.
"""
import os
import questionary
from rich.console import Console
from mle.model import load_model
from mle.utils import print_in_box, ask_text, WorkflowCache
from mle.agents import CodeAgent, DebugAgent, AdviseAgent, PlanAgent


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


def baseline(work_dir: str, model=None):
    """
    The workflow of the baseline mode.
    :return:
    """

    console = Console()
    cache = WorkflowCache(work_dir, 'baseline')
    model = load_model(work_dir, model)

    if not cache.is_empty():
        step = ask_text(f"MLE has finished the following steps: \n{cache}\n"
                        f"You can pick a step from 1 to {cache.current_step()} to resume\n"
                        "(or ENTER to continue the workflow)")
        if step:
            step = int(step)
            for i in range(step, cache.current_step() + 1):
                cache.remove(i)  # remove the stale step caches

    # ask for the data information
    with cache(step=1, name="ask for the data information") as ca:
        dataset = ca.resume("dataset")
        if dataset is None:
            advisor = AdviseAgent(model, console)
            dataset = ask_text("Please provide your dataset information (a public dataset name or a local file path)")
            if not dataset:
                print_in_box("The dataset is empty. Aborted", console, title="Error", color="red")
                return
            dataset = advisor.clarify_dataset(dataset)
            ca.store("dataset", dataset)

    # ask for the user requirement
    with cache(step=2, name="ask for the user requirement") as ca:
        ml_requirement = ca.resume("ml_requirement")
        if ml_requirement is None:
            ml_requirement = ask_text("Please provide your requirement")
            if not ml_requirement:
                print_in_box("The user's requirement is empty. Aborted", console, title="Error", color="red")
                return
        ca.store("ml_requirement", ml_requirement)

    # advisor agent gives suggestions in a report
    with cache(step=3, name="MLE advisor agent provides a high-level report") as ca:
        advisor_report = ca.resume("advisor_report")
        if advisor_report is None:
            advisor = AdviseAgent(model, console)
            advisor_report = advisor.interact("[green]User Requirement:[/green] " + ml_requirement + "\n" + ask_data(dataset))
        ca.store("advisor_report", advisor_report)

    # plan agent generates the coding plan
    with cache(step=4, name="MLE plan agent generates a dev plan") as ca:
        coding_plan = ca.resume("coding_plan")
        if coding_plan is None:
            planner = PlanAgent(model, console)
            coding_plan = planner.interact(advisor_report)
        ca.store("coding_plan", coding_plan)

    # code agent codes the tasks and debug with the debug agent
    with cache(step=5, name="MLE code&debug agents start to work") as ca:
        coder = CodeAgent(model, work_dir, console)
        coder.read_requirement(advisor_report)
        debugger = DebugAgent(model, console)

        is_auto_mode = questionary.confirm(
            "MLE developer is about to start to code.\n"
            "Choose to debug or not (If no, MLE agent will only focus on coding tasks,"
            " and you have to run and debug the code yourself)?"
        ).ask()

        for current_task in coding_plan.get('tasks'):
            code_report = coder.interact(current_task)
            is_debugging = code_report.get('debug')

            if is_auto_mode:
                while True:
                    if is_debugging == 'true' or is_debugging == 'True':
                        with console.status("MLE Debug Agent is executing and debugging the code..."):
                            debug_report = debugger.analyze(code_report)
                        if debug_report.get('status') == 'success':
                            break
                        else:
                            code_report = coder.debug(current_task, debug_report)
                    else:
                        break
