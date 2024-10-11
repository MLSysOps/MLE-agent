"""
Kaggle Mode: the mode to generate ML pipeline for kaggle competitions.
"""
import os
import questionary
from rich.console import Console
from mle.model import load_model
from mle.utils import ask_text, WorkflowCache
from mle.agents import CodeAgent, DebugAgent, AdviseAgent, PlanAgent, SummaryAgent
from mle.integration import KaggleIntegration


def kaggle(work_dir: str, model=None, kaggle_username=None, kaggle_token=None):
    """
    The workflow of the kaggle mode.
    """
    console = Console()
    cache = WorkflowCache(work_dir, 'kaggle')
    model = load_model(work_dir, model)
    kaggle = KaggleIntegration(kaggle_username, kaggle_token)

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
                choices=kaggle.list_competition()
            ).ask()
            with console.status("MLE Agent is downloading the kaggle competition dataset..."):
                dataset = kaggle.download_competition_dataset(
                    competition, os.path.join(os.getcwd(), 'data'))
        ca.store("competition", competition)
        ca.store("dataset", dataset)

    # ask for the user requirement
    with cache(step=2, name="get the competition overview from kaggle") as ca:
        ml_requirement = ca.resume("ml_requirement")
        if ml_requirement is None:
            with console.status("MLE Agent is fetching the kaggle competition overview..."):
                overview = kaggle.get_competition_overview(competition)
                summary = SummaryAgent(model, console=console)
                ml_requirement = summary.kaggle_request_summarize(overview)
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
