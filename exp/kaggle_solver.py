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
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from langgraph.checkpoint.memory import MemorySaver
from rich.console import Console
from rich.pretty import Pretty

from langgraph.func import task, entrypoint
from rich.syntax import Syntax

from exp.utils import build_tree_dict, find_existing_venv, create_virtualenv
from exp.agents import AdviseAgent, PlanAgent, CodeAgent

from mlebench.registry import registry

from mle.function import read_file
from mle.utils import print_in_box


# -----------------------------------------------------------------------------
# Shared‑state dataclass
# -----------------------------------------------------------------------------
@dataclass
class KaggleState:
    # singletons -------------------------------------------------------------
    work_dir: str
    model: Any | None = None

    # dataset and competition info -------------------------------------------
    competition_id: str | None = None
    competition_type: str | None = None
    dataset_path: Path | None = None
    description: str | None = None
    sample_submission: str = None
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
        state.competition_type = competition.competition_type
        state.description = competition.description
        state.sample_submission = competition.sample_submission.as_posix()
        console.log(f"[bold green]Competition {state.competition_id} loaded successfully![/bold green]")
    else:
        raise ValueError(
            f"Competition with ID '{state.competition_id}' not found in MLE Bench"
        )

    state.model = inputs.get("model", None)

    return state


@task
def setup_environment(state: KaggleState) -> dict[str, Any]:
    """
    Set up the environment for the Kaggle competition.
    This function can be extended to install dependencies, set up virtual environments, etc.
    """
    console.log(f"Setting up environment for {state.competition_id}...")
    # List out the dataset structure, and each file content
    dataset_structure = build_tree_dict(state.dataset_path)
    # Set up a virtual environment at the working directory (if not exists)
    if py_exe := find_existing_venv(state.work_dir):
        console.log(f"Found existing virtual environment")
    else:
        console.log("No existing virtual environment found, creating...")
        py_exe = create_virtualenv(cwd=state.work_dir)
    console.log(f"Using Python executable: {py_exe}")
    # Report the venv metadata
    py_version = subprocess.check_output([py_exe, "--version"], text=True).strip()
    console.log(f"Python version: {py_version}")
    return {
        "dataset_path": str(state.dataset_path),
        "dataset_structure": dataset_structure,
        "python_env": {
            "executable": str(py_exe),
            "version": py_version,
        },
    }


@entrypoint(checkpointer=MemorySaver())
def kaggle_solver(inputs: dict) -> KaggleState:
    """Run the entire Kaggle workflow in functional‑API style."""
    # create initial state
    state = init_node(inputs).result()
    env_dict = setup_environment(state).result()

    # Create agents
    advisor = AdviseAgent(model_name=state.model, console=console)
    planer = PlanAgent(model_name=state.model, working_dir=state.work_dir, console=console)
    coder = CodeAgent(model_name=state.model, working_dir=state.work_dir, console=console)

    advisor_report = advisor.graph.invoke(
        advisor.State(
            env=env_dict,
            competition_type=state.competition_type,
            description=state.description,
            submission_file=state.sample_submission,
            sample_submission_file=state.sample_submission,
        )
    )
    print_in_box(
        Pretty(advisor_report), console, title="MLE Advisor Report", color="blue"
    )

    coding_plan = planer.graph.invoke(
        planer.State(
            advisor_report=advisor_report,
            env=env_dict,
            submission_file=state.sample_submission,
            sample_submission_file=state.sample_submission,
        )
    )
    print_in_box(
        Pretty(coding_plan), console, title="MLE Coding Plan", color="purple"
    )

    # coding plan loop
    while tasks := coding_plan.get("tasks"):
        current_task = tasks.pop(0)
        code_report = coder.graph.invoke(
            CodeAgent.State(
                task=current_task.get("task", ""),
                description=current_task.get("description", ""),
                advisor_report=advisor_report,
                plan=coding_plan,
                env=env_dict,
            ),
        )
        print_in_box(
            Pretty(code_report), console, title="MLE Code Report", color="yellow"
        )
        # Print the code
        console.log(f"Generated code for task: {current_task.get('task', '')}")
        if (python_file := code_report.get("entryfile", None)) is not None:
            python_code = read_file(
                Path(state.work_dir).absolute() / python_file,
            )
            console.print(Syntax(python_code, "python", word_wrap=True))

        # Note: disable debugging for now
        # while True:
        #     if state.debug_attempt > state.debug_max_attempt:
        #         console.log(
        #             f"Debug the code failed with max {state.debug_max_attempt} attempts. Please check the code manually."
        #         )
        #         break
        #
        #     state = debug(state).result()
        #     state.debug_attempt += 1

    # finished
    if console:
        console.print("[bold green]Kaggle workflow completed![/bold green]")

    return state


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Run Kaggle workflow (functional API)")
    p.add_argument("work_dir")
    p.add_argument("--model", default='Qwen/Qwen3-8B-AWQ', )
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
    kaggle_solver.invoke(vars(args), config=config)
