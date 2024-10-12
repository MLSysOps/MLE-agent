"""
Kaggle Mode: the mode to generate ML pipeline for kaggle competitions.
"""
import os
import questionary
from typing import List
from rich.console import Console

from mle.model import load_model
from mle.function import execute_command
from mle.integration import KaggleIntegration
from mle.utils import ask_text, read_markdown, is_markdown_file, WorkflowCache, print_in_box
from mle.agents import CodeAgent, DebugAgent, AdviseAgent, PlanAgent, SummaryAgent


def auto_kaggle(
        work_dir: str,
        datasets: List[str],
        description: str,
        submission='./submission.csv',
        sub_examples=None,
        competition_id=None,
        model=None
):
    """
    The workflow of the kaggle mode.
    :param work_dir: the working directory.
    :param datasets: the datasets to use.
    :param description: the description of the competition, can be a path to a local .md file or a string.
    :param submission: the path of the kaggle submission file.
    :param sub_examples: the path to the kaggle submission example file.
    :param competition_id: the competition id.
    :param model: the model to use.
    """
    console = Console()
    model = load_model(work_dir, model)

    # initialize the agents
    advisor = AdviseAgent(model, console, mode="precise")
    summarizer = SummaryAgent(model, console=console)
    coder = CodeAgent(model, work_dir, console=console, single_file=True)
    debugger = DebugAgent(model, console, analyze_only=True)

    if is_markdown_file(description):
        description = read_markdown(description)

    with console.status("MLE Agent is processing the kaggle competition overview..."):
        requirements = summarizer.kaggle_request_summarize(description, sub_examples)
        requirements += f"\n\nLOCAL DATASET PATH:\n"
        for dataset in datasets:
            requirements += f" - {dataset}\n"

        requirements += f"\nSUBMISSION FILE PATH: {submission}\n"

    suggestions = advisor.suggest(requirements, return_raw=True)
    requirements += f"""
    \nIMPLEMENTATION SUGGESTIONS:
    
- Suggestion summary: {suggestions.get('suggestion')}
- ML task: {suggestions.get('task')}
- Model or algorithm: {suggestions.get('model_or_algorithm')}
- Training strategy: {suggestions.get('training_method')}
- Tricks to increase performance:
"""
    for trick in suggestions.get('tricks'):
        requirements += f"\n  - {trick}"

    coder.read_requirement(requirements)
    if competition_id is None:
        competition_id = "kaggle competition"

    coding_task = {
        "task": competition_id,
        "description": requirements
    }
    print_in_box(requirements, console, title="Kaggle Competition Requirement", color="green")
    code_report = coder.code(coding_task)
    while True:
        with console.status("MLE Debug Agent is executing and debugging the code..."):
            running_cmd = code_report.get('command')
            logs = execute_command(running_cmd)
            debug_report = debugger.analyze_with_log(running_cmd, logs)
        if debug_report.get('status') == 'success':
            # check the submission file
            if not os.path.exists(submission):
                console.log(f"The submission file ({submission}) is not found. Launch the coder to improve...")
                code_report = coder.debug(
                    coding_task,
                    {
                        "status": "error",
                        "changes": [
                            f"make sure the submission file is generated in {submission}",
                            f"make sure the submission file is in the correct format. You can refer to the example submission file: {sub_examples}"
                        ],
                        "suggestion": f"Please update the code related to generating the submission file."
                    }
                )
            else:
                break
        else:
            code_report = coder.debug(coding_task, debug_report)


def kaggle(work_dir: str, model=None):
    """
    The workflow of the kaggle mode.
    :param work_dir: the working directory.
    :param model: the model to use.
    """
    console = Console()
    cache = WorkflowCache(work_dir, 'kaggle')
    model = load_model(work_dir, model)
    integration = KaggleIntegration()

    if not cache.is_empty():
        step = ask_text(f"MLE has finished the following steps: \n{cache}\n"
                        f"You can pick a step from 1 to {cache.current_step()} to resume\n"
                        "(or ENTER to continue the workflow)")
        if step:
            step = int(step)
            for i in range(step, cache.current_step() + 1):
                cache.remove(i)  # remove the stale step caches

    # ask for the kaggle competition
    with cache(step=1, name="ask for the kaggle competition") as ca:
        competition = ca.resume("competition")
        dataset = ca.resume("dataset")
        if competition is None or dataset is None:
            competition = questionary.select(
                "Please select a Kaggle competition to join:",
                choices=integration.list_competition()
            ).ask()
            with console.status("MLE Agent is downloading the kaggle competition dataset..."):
                dataset = integration.download_competition_dataset(
                    competition, os.path.join(os.getcwd(), 'data'))
        ca.store("competition", competition)
        ca.store("dataset", dataset)

    # ask for the user requirement
    with cache(step=2, name="get the competition overview from kaggle") as ca:
        ml_requirement = ca.resume("ml_requirement")
        if ml_requirement is None:
            with console.status("MLE Agent is fetching the kaggle competition overview..."):
                summary = SummaryAgent(model, console=console)
                ml_requirement = summary.kaggle_request_summarize(integration.fetch_competition_overview(competition))
        ca.store("ml_requirement", ml_requirement)

    # advisor agent gives suggestions in a report
    with cache(step=3, name="MLE advisor agent provides a high-level report") as ca:
        advisor_report = ca.resume("advisor_report")
        if advisor_report is None:
            advisor = AdviseAgent(model, console)
            advisor_report = advisor.interact(
                f"[green]Competition Requirement:[/green] {ml_requirement}\n"
                f"Dataset is downloaded in path: {dataset}"
            )
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
