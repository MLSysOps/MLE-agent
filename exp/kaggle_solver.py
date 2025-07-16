"""
Author: Yuanming Li
Email: yuanmingleee@gmail.com
Date: Jul 15, 2025

LangGraph refactor of the original `kaggle()` workflow.

This implementation keeps the previous modular design—each agent/tool is wrapped
in a small, single‑purpose function (node), so contributors can read or swap
logic easily. It uses LangGraph's **functional API** (each node is just a
callable that receives and returns a shared state).

How to run
~~~~~~~~~~
```bash
python kaggle_langgraph_functional.py /path/to/work_dir --model my_llm
```

Or import and call directly:
```python
from kaggle_langgraph_functional import kaggle_solver
kaggle_solver.invoke("/tmp/kaggle")
```
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Iterable

from rich.console import Console
import questionary

from langgraph.func import task, entrypoint

from mle.cli import console
from mle.function import execute_command
from mle.model import load_model
from mle.agents import (
    WorkflowCache,
    GitHubSummaryAgent,
    AdviseAgent,
    PlanAgent,
    CodeAgent,
    DebugAgent,
)

from mlebench.registry import registry


# -----------------------------------------------------------------------------
# Shared‑state dataclass
# -----------------------------------------------------------------------------
@dataclass
class KaggleState:
    work_dir: str
    # singletons -------------------------------------------------------------
    console: Console | None = None
    cache: WorkflowCache | None = None
    model: Any | None = None
    # Agents
    advisor: AdviseAgent | None = None
    planner: PlanAgent | None = None
    coder: CodeAgent | None = None
    debugger: DebugAgent | None = None

    # run‑time ---------------------------------------------------------------
    resume_step: int | None = None
    # dataset and competition info -------------------------------------------
    competition_id: str | None = None
    dataset_path: str | None = None
    description: str | None = None
    ml_requirement: str | None = None
    # MLE agents' outputs ----------------------------------------------------
    advisor_report: str | None = None
    coding_plan: Dict[str, Any] | None = None
    is_auto_mode: bool | None = None

    # coding ------------------------------------------------------------
    current_task: Dict[str, Any] | None = None
    code_report: Dict[str, Any] | None = None
    debug_attempt: int = 0
    debug_max_attempt: int = 5

    # output files -----------------------------------------------------------
    submission: str = "submission.csv"
    sample_submission: str = None


# -----------------------------------------------------------------------------
# Task nodes
# -----------------------------------------------------------------------------

@task
def init_node(inputs: dict) -> KaggleState:
    state = KaggleState(
        work_dir=inputs.get("work_dir", os.getcwd()),
        model=inputs.get("model", None),
        competition_id=inputs.get("competition", None),
    )
    state.console = Console()
    state.cache = WorkflowCache(state.work_dir, "kaggle")
    try:
        state.model = load_model(state.work_dir, state.model)
    except Exception as e:
        state.console.print(f"[bold red]Error loading model: {e}[/bold red]")
        raise e

    # Load MLE Bench kaggle competition by id
    if competition := registry.get_competition(state.competition_id):
        console.print(competition)
        state.dataset_path = competition.public_dir
        state.description = competition.description
    else:
        raise ValueError(
            f"Competition with ID '{state.competition_id}' not found in MLE Bench"
        )

    # Load agents
    state.advisor = AdviseAgent(model=state.model, working_dir=state.work_dir, console=state.console)
    state.planner = PlanAgent(model=state.model, working_dir=state.work_dir, console=state.console)
    state.coder = CodeAgent(model=state.model, working_dir=state.work_dir, console=state.console)
    state.debugger = DebugAgent(model=state.model, console=state.console)

    return state


@task
def resume_decision_node(state: KaggleState) -> KaggleState:
    cache = state.cache
    if cache and not cache.is_empty():
        step = questionary.text(
            f"MLE has finished the following steps:\n{cache}\n"
            f"Pick a step from 1 to {cache.current_step()} to resume (or ENTER to continue)"
        ).ask()
        if step:
            state.resume_step = int(step)
            for i in range(state.resume_step, cache.current_step() + 1):
                cache.remove(i)
    return state


@task
def overview_summary_node(state: KaggleState) -> KaggleState:
    cache, con = state.cache, state.console
    with cache(step=2, name="get the competition overview from kaggle") as ca:
        state.ml_requirement = ca.resume("ml_requirement")
        if state.ml_requirement is None:
            summary = GitHubSummaryAgent(state.model, console=con)
            state.ml_requirement = summary.kaggle_request_summarize(state.description)
        ca.store("ml_requirement", state.ml_requirement)
    return state


@task
def advisor_report_node(state: KaggleState) -> KaggleState:
    with (state.cache(step=3, name="MLE advisor agent provides a high‑level report") as ca):
        state.advisor_report = ca.resume("advisor_report")
        if state.advisor_report is None:
            with console.status("MLE Agent is processing the kaggle competition overview..."):
                requirements = state.ml_requirement + f"\nDataset path: {state.dataset_path}" \
                               + f"\nSUBMISSION FILE PATH: {state.submission}\n"

            state.advisor_report = state.advisor.suggest(
                requirements, return_raw=True
            )
        ca.store("advisor_report", state.advisor_report)
    return state


@task
def plan_generation_node(state: KaggleState) -> KaggleState:
    with state.cache(step=4, name="MLE plan agent generates a dev plan") as ca:
        state.coding_plan = ca.resume("coding_plan")
        if state.coding_plan is None:
            state.coding_plan = state.planner.interact(state.advisor_report)
        ca.store("coding_plan", state.coding_plan)
    return state


@task
def coder_read_requirement(state: KaggleState) -> KaggleState:
    state.coder.read_requirement(state.advisor_report)
    return state


@task
def code_task_node(state: KaggleState) -> KaggleState:
    state.code_report = state.coder.code(state.current_task)
    return state


@task
def debug(state: KaggleState) -> KaggleState:
    # TODO: save the code to a file, create a venvironment, and run it
    #  collect the run logs and errors
    with console.status("MLE Debug Agent is executing and debugging the code..."):
        running_cmd = state.code_report.get('command')
        logs = execute_command(running_cmd)
        debug_report = state.debugger.analyze_with_log(running_cmd, logs)
        state.code_report = state.coder.debug(state.current_task, debug_report)
    return state


@task
def check_submission_file(state: KaggleState) -> KaggleState:
    if not os.path.exists(state.submission):
        console.log(f"The submission file ({state.submission}) is not found. Please check the code.")
        state.code_report = state.coder.debug(
            state.current_task,
            {
                "status": "error",
                "changes": [
                    f"make sure the submission file is generated in {state.submission}",
                    f"make sure the submission file is in the correct format. You can refer to the example "
                    f"submission file: {state.sample_submission}"
                ],
                "suggestion": f"Please update the code related to generating the submission file."
            }
        )
    return state


@entrypoint()
def kaggle_solver(inputs: dict) -> KaggleState:
    """Run the entire Kaggle workflow in functional‑API style."""
    # create initial state
    state = init_node(inputs).result()

    # sequential pre‑coding steps
    for step_fn in (
            resume_decision_node,
            overview_summary_node,
            advisor_report_node,
            plan_generation_node,
            coder_read_requirement,
    ):
        state = step_fn(state).result()

    # coding plan loop
    while state.coding_plan and (tasks := state.coding_plan.get("tasks")):
        state.current_task = tasks.pop(0)
        state = code_task_node(state).result()
        while True:
            if state.debug_attempt > state.debug_max_attempt:
                console.log(
                    f"Debug the code failed with max {state.debug_max_attempt} attempts. Please check the code manually."
                )
                break

            state = debug(state).result()
            state.debug_attempt += 1

    # finished
    if state.console:
        state.console.print("[bold green]Kaggle workflow completed![/bold green]")
    return state


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Run Kaggle workflow (functional API)")
    p.add_argument("work_dir")
    p.add_argument("--model", default='Qwen/Qwen2.5-1.5B-Instruct')
    p.add_argument(
        "--competition", "-c",
        help="MLE Bench competition ID to run",
    )
    args = p.parse_args()
    kaggle_solver.invoke(vars(args))
