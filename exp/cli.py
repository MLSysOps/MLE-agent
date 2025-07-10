#!/usr/bin/env python3
"""Experimental CLI bridging MLE‑agent and MLE‑bench (GitHub version).

This *minimal‑touch* wrapper lets the MLE‑agent interact with MLE‑bench even
though **mle‑bench isn’t on PyPI yet**.  We install it straight from GitHub and
expose familiar commands similar to the existing Kaggle helpers:

* **install** – grab/upgrade *mle‑bench* via `pip install git+…`
* **prepare** – `mle‑bench dataset prepare …` (fallback to Kaggle)
* **run** – run a benchmark → `submission.csv`
* **grade** – local scoring via `mlebench grade-sample`

Place this single file under `<repo‑root>/exp/` to keep the core project
untouched while enabling fast experimentation.
"""
from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional

from install import install as install_mlebench

import click

LOGGER = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

ROOT = Path(__file__).resolve().parent.parent
EXP_DIR = ROOT / "exp"
GIT_URI = "git+https://github.com/openai/mle-bench.git"


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _run(cmd: list[str], cwd: Optional[Path] = None) -> None:
    """Run *cmd* with logging; abort on non‑zero exit."""
    LOGGER.info("Running command: %s", " ".join(map(str, cmd)))
    result = subprocess.run(cmd, cwd=cwd or ROOT)
    if result.returncode != 0:
        LOGGER.error("Command failed with exit code %s", result.returncode)
        sys.exit(result.returncode)


def _detect_mle_bench() -> bool:
    """Return *True* if `mle-bench` binary appears runnable."""
    try:
        import mlebench
        return True
    except ImportError:
        LOGGER.warning("mlebench package not found. Please install it first.")
        return False


# ---------------------------------------------------------------------------
# CLI definition
# ---------------------------------------------------------------------------

@click.group()
def cli():
    pass

@cli.command(
    # forward *everything* after “bench …”
    context_settings={
        "ignore_unknown_options": True,
        "allow_extra_args": True,
        "help_option_names": []      # DISABLE Click’s -h/--help here
        # (equivalent to add_help_option=False on older Click)
    },
)
@click.pass_context
def bench(ctx):
    """
    Proxy everything after `bench` to the external command `mlebench`.
    """
    if not ctx.args:
        ctx.args = ["--help"]

    if not _detect_mle_bench():
        LOGGER.error("MLE-bench is not installed. Please run `mle bench install` first.")
        sys.exit(1)
    # ctx.args now contains whatever followed 'bench'
    cmd = ["mlebench", *ctx.args]              # build the real command line
    # forward the child’s exit-status back to the shell
    sys.exit(subprocess.call(cmd))


if __name__ == "__main__":  # pragma: no cover
    cli()
