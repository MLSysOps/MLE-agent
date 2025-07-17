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
import uuid
from dataclasses import dataclass
from typing import Any, Dict

from langgraph.checkpoint.memory import MemorySaver
from rich.console import Console
from rich.pretty import Pretty
from rich.markdown import Markdown

from langgraph.func import task, entrypoint

from mle.cli import console
from mle.function import execute_command
from mle.model import load_model
from mle.agents import (
    GitHubSummaryAgent,
    AdviseAgent,
    PlanAgent,
    CodeAgent,
    DebugAgent,
)

from mlebench.registry import registry

from mle.utils import print_in_box


# -----------------------------------------------------------------------------
# Shared‑state dataclass
# -----------------------------------------------------------------------------
@dataclass
class KaggleState:
    # singletons -------------------------------------------------------------
    work_dir: str
    model: Any | None = None

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
        competition_id=inputs.get("competition", None),
    )
    # Load MLE Bench kaggle competition by id
    if competition := registry.get_competition(state.competition_id):
        state.dataset_path = competition.public_dir
        state.description = competition.description
        console.print(f"[bold green]Competition {state.competition_id} loaded successfully![/bold green]")
    else:
        raise ValueError(
            f"Competition with ID '{state.competition_id}' not found in MLE Bench"
        )

    return state


@task
def overview_summary_node(state: KaggleState) -> KaggleState:
    summary = GitHubSummaryAgent(model, console=console)
    state.ml_requirement = summary.kaggle_request_summarize(state.description)
    return state


@task
def advisor_report_node(state: KaggleState) -> KaggleState:
    requirements = state.ml_requirement + f"\nDataset path: {state.dataset_path}" \
                   + f"\nSUBMISSION FILE PATH: {state.submission}\n"

    advisor = AdviseAgent(model=model, working_dir=state.work_dir, console=console)
    state.advisor_report = advisor.suggest(requirements)
    print_in_box(
        Markdown(state.advisor_report), console, title="MLE Advisor Report", color="blue"
    )
    return state


@task
def plan_generation_node(state: KaggleState) -> KaggleState:
    planer = PlanAgent(model=model, working_dir=state.work_dir, console=console)
    state.coding_plan = planer.plan(state.advisor_report)
    print_in_box(
        Pretty(state.coding_plan), console, title="MLE Coding Plan", color="purple"
    )
    return state


@task
def code_task_node(state: KaggleState) -> KaggleState:
    coder = CodeAgent(
        model=model, working_dir=state.work_dir, console=console,
        single_file=True,
    )
    coder.read_requirement(state.advisor_report)
    state.code_report = coder.code(state.current_task)
    console.print(state.code_report)
    return state


@task
def debug(state: KaggleState) -> KaggleState:
    # TODO: save the code to a file, create a venvironment, and run it
    #  collect the run logs and errors
    coder = CodeAgent(
        model=model, working_dir=state.work_dir, console=console,
        single_file=True,
    )
    debugger = DebugAgent(model=model, console=console)
    with console.status("MLE Debug Agent is executing and debugging the code..."):
        running_cmd = state.code_report.get('command')
        logs = execute_command(running_cmd)
        debug_report = debugger.analyze_with_log(running_cmd, logs)
        state.code_report = coder.debug(state.current_task, debug_report)
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


@entrypoint(checkpointer=MemorySaver())
def kaggle_solver(inputs: dict) -> KaggleState:
    """Run the entire Kaggle workflow in functional‑API style."""
    # create initial state
    state = init_node(inputs).result()

    # sequential pre‑coding steps
    for step_fn in (
            overview_summary_node,
            advisor_report_node,
            plan_generation_node,
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
    if console:
        console.print("[bold green]Kaggle workflow completed![/bold green]")

    console.print(state)
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

    config = {
        "configurable": {
            "thread_id": str(uuid.uuid4())
        },
    }
    console = Console()
    try:
        model = load_model(args.work_dir, args.model)
    except Exception as e:
        console.print(f"[bold red]Error loading model: {e}[/bold red]")
        raise e
    kaggle_solver.invoke(vars(args), config=config)

    history = list(kaggle_solver.get_state_history(config))
    for state in history:
        console.print(state)
