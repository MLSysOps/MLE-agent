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

import langgraph
from langgraph import task, router, entrypoint  # functional API decorators

from mle.integration import KaggleIntegration
from mle.model import load_model
from mle.agents import (
    WorkflowCache,
    GitHubSummaryAgent,
    AdviseAgent,
    PlanAgent,
    CodeAgent,
    DebugAgent,
)

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
    integration: KaggleIntegration | None = None

    # run‑time ---------------------------------------------------------------
    resume_step: int | None = None
    competition: str | None = None
    dataset_path: str | None = None
    ml_requirement: str | None = None
    advisor_report: str | None = None
    coding_plan: Dict[str, Any] | None = None
    is_auto_mode: bool | None = None

    # coding loop ------------------------------------------------------------
    current_task: Dict[str, Any] | None = None
    code_report: Dict[str, Any] | None = None
    final_code_reports: List[Dict[str, Any]] = field(default_factory=list)

# -----------------------------------------------------------------------------
# Task nodes
# -----------------------------------------------------------------------------

@task()
def init_node(state: KaggleState) -> KaggleState:
    state.console = Console()
    state.cache = WorkflowCache(state.work_dir, "kaggle")
    state.model = load_model(state.work_dir, state.model)
    state.integration = KaggleIntegration()
    return state

@task()
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

@task()
def select_competition_node(state: KaggleState) -> KaggleState:
    cache, integ, con = state.cache, state.integration, state.console
    with cache(step=1, name="ask for the kaggle competition") as ca:
        state.competition = ca.resume("competition")
        state.dataset_path = ca.resume("dataset")
        if not (state.competition and state.dataset_path):
            state.competition = questionary.select(
                "Please select a Kaggle competition to join:",
                choices=integ.list_competition(),
            ).ask()
            with con.status("Downloading competition dataset …"):
                state.dataset_path = integ.download_competition_dataset(
                    state.competition, os.path.join(os.getcwd(), "data")
                )
        ca.store("competition", state.competition)
        ca.store("dataset", state.dataset_path)
    return state

@task()
def overview_summary_node(state: KaggleState) -> KaggleState:
    cache, integ, con = state.cache, state.integration, state.console
    with cache(step=2, name="get the competition overview from kaggle") as ca:
        state.ml_requirement = ca.resume("ml_requirement")
        if state.ml_requirement is None:
            with con.status("Fetching competition overview …"):
                summary = GitHubSummaryAgent(state.model, console=con)
                overview_md = integ.fetch_competition_overview(state.competition)
                state.ml_requirement = summary.kaggle_request_summarize(overview_md)
        ca.store("ml_requirement", state.ml_requirement)
    return state

@task()
def advisor_report_node(state: KaggleState) -> KaggleState:
    cache, con = state.cache, state.console
    with cache(step=3, name="MLE advisor agent provides a high‑level report") as ca:
        state.advisor_report = ca.resume("advisor_report")
        if state.advisor_report is None:
            advisor = AdviseAgent(state.model, con)
            state.advisor_report = advisor.interact(
                f"[green]Competition Requirement:[/green] {state.ml_requirement}\n"
                f"Dataset path: {state.dataset_path}"
            )
        ca.store("advisor_report", state.advisor_report)
    return state

@task()
def plan_generation_node(state: KaggleState) -> KaggleState:
    cache, con = state.cache, state.console
    with cache(step=4, name="MLE plan agent generates a dev plan") as ca:
        state.coding_plan = ca.resume("coding_plan")
        if state.coding_plan is None:
            planner = PlanAgent(state.model, con)
            state.coding_plan = planner.interact(state.advisor_report)
        ca.store("coding_plan", state.coding_plan)
    return state

# ---------- Coding helpers ---------------------------------------------------

def _ensure_auto_mode(state: KaggleState):
    if state.is_auto_mode is None:
        state.is_auto_mode = questionary.confirm(
            "MLE developer is about to start to code.\nChoose to debug or not? (No = code‑only mode)"
        ).ask()

@task()
def code_task_node(state: KaggleState) -> KaggleState:
    _ensure_auto_mode(state)
    coder = CodeAgent(state.model, state.work_dir, state.console)
    coder.read_requirement(state.advisor_report)

    tasks: Iterable[Dict[str, Any]] = state.coding_plan.get("tasks", [])
    if not tasks:
        return state
    state.current_task = tasks.pop(0)
    state.code_report = coder.interact(state.current_task)
    return state

@router()
def debug_decision_node(state: KaggleState) -> str:
    _ensure_auto_mode(state)
    needs_debug = (
        state.is_auto_mode and state.code_report and
        str(state.code_report.get("debug", "")).lower() == "true"
    )
    return "debug" if needs_debug else "done"

@task()
def debug_loop_node(state: KaggleState) -> KaggleState:
    debugger = DebugAgent(state.model, state.console)
    coder = CodeAgent(state.model, state.work_dir, state.console)
    while True:
        with state.console.status("Debugging code …"):
            debug_report = debugger.analyze(state.code_report)
        if debug_report.get("status") == "success":
            break
        state.code_report = coder.debug(state.current_task, debug_report)
    return state

# -----------------------------------------------------------------------------
# Entrypoint orchestrator – mirrors the example provided by the user
# -----------------------------------------------------------------------------

@entrypoint()
def kaggle_solver(work_dir: str, model: Any | None = None):
    """Run the entire Kaggle workflow in functional‑API style."""
    # create initial state
    state = KaggleState(work_dir=work_dir, model=model)

    # sequential pre‑coding steps
    for step_fn in (
        init_node,
        resume_decision_node,
        select_competition_node,
        overview_summary_node,
        advisor_report_node,
        plan_generation_node,
    ):
        state = step_fn(state).result()

    # coding plan loop
    while state.coding_plan and state.coding_plan.get("tasks"):
        state = code_task_node(state).result()
        route = debug_decision_node(state).result()
        if route == "debug":
            state = debug_loop_node(state).result()

    # finished
    if state.console:
        state.console.print("[bold green]Kaggle workflow completed![/bold green]")
    return state


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Run Kaggle workflow (functional API)")
    p.add_argument("work_dir")
    p.add_argument("--model")
    args = p.parse_args()
    kaggle_solver.invoke(args.work_dir)
