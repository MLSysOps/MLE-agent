#!/usr/bin/env python3
"""Experimental CLI bridging MLE‑agent and MLE‑bench (GitHub version).

This *minimal‑touch* wrapper lets the MLE‑agent interact with MLE‑bench even
though **mle‑bench isn’t on PyPI yet**.  We install it straight from GitHub and
expose familiar commands similar to the existing Kaggle helpers:

* **init** – Init *mle‑bench* via patching the missing LFS MLE-agent package

* **prepare** – `mle‑bench dataset prepare …`

* **grade** – local scoring via `mlebench grade`

* **grade-sample** – local scoring of a single competition via
  `mlebench grade-sample`

Place this single file under `<repo‑root>/exp/` to keep the core project
untouched while enabling fast experimentation.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import mle
from exp.init import init as init_api, is_init

import click


try:
    import mlebench
except ImportError:
    click.echo("mlebench package not found. Please install it first.", err=True)
    sys.exit(1)


from mlebench.registry import registry
from exp.mlebench_api import (
    grade as grade_api,
    grade_sample as grade_sample_api,
    prepare as prepare_api
)


def require_init(f):
    @click.pass_context
    def wrapper(ctx, *args, **kwargs):
        if not is_init():
            click.echo("Error: setup is not done. Please run `mle-exp setup` first.", err=True)
            ctx.exit(1)
        return ctx.invoke(f, *args, **kwargs)
    return wrapper


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=False,
)
@click.pass_context
@click.version_option(version=mle.__version__)
def cli(ctx: click.Context):
    """
    MLE-Exp: The Experimental CLI tool for MLE-agent.
    """
    ctx.obj = {"registry": registry}


@cli.command(
    name="init",
    short_help="Initialize MLE-bench",
)
@click.option(
    "--force", "-f",
    is_flag=True,
    help="Force re-initialize MLE-bench",
)
def init(force: bool):
    """
    Init or upgrade MLE-bench from GitHub.

    This command installs the MLE-bench package directly from the GitHub repository.
    If MLE-bench is already installed, it will force re-setup if the `--force` flag is provided.
    """
    sys.exit(init_api(force))


@cli.command("prepare", help="Download and prepare one or more competitions.")
@click.option(
    "-c",
    "--competition-id",
    metavar="ID",
    type=str,
    help=f"ID of the competition to prepare. "
    f"Valid options: {registry.list_competition_ids()}",
)
@click.option(
    "-a",
    "--all",
    "prepare_all",
    is_flag=True,
    help="Prepare **all** competitions.",
)
@click.option(
    "--lite",
    is_flag=True,
    help="Prepare only the low-complexity (Lite) set of competitions.",
)
@click.option(
    "-l",
    "--list",
    "list_file",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
    help="Text file containing one competition ID per line.",
)
@click.option(
    "--keep-raw",
    is_flag=True,
    help="Keep the raw competition files after preparation.",
)
@click.option(
    "--data-dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=registry.get_data_dir(),
    show_default=True,
    help="Directory where the data should live.",
)
@click.option(
    "--overwrite-checksums", is_flag=True, help="[Dev] Overwrite checksums file."
)
@click.option(
    "--overwrite-leaderboard", is_flag=True, help="[Dev] Overwrite leaderboard."
)
@click.option("--skip-verification", is_flag=True, help="[Dev] Skip checksum checks.")
@click.pass_context
@require_init
def prepare(
    ctx: click.Context,
    competition_id: str | None,
    prepare_all: bool,
    lite: bool,
    list_file: Path | None,
    keep_raw: bool,
    data_dir: Path,
    overwrite_checksums: bool,
    overwrite_leaderboard: bool,
    skip_verification: bool,
) -> None:
    # Set PYTHONUTF8 for Windows to ensure UTF-8 encoding for file operations
    from pathlib import Path as _Path

    _restore_patch = None
    if sys.platform == "win32" and not getattr(_Path, "_utf8_patched", False):
        _orig_read_text = _Path.read_text

        def _read_text_utf8(self, *args, **kwargs):  # type: ignore[override]
            kwargs.setdefault("encoding", "utf-8")
            return _orig_read_text(self, *args, **kwargs)

        _Path.read_text = _read_text_utf8
        _restore_patch = lambda: setattr(_Path, "read_text", _orig_read_text)

    try:
        ctx.obj["registry"].set_data_dir(Path(data_dir))

        prepare_api(
            competition_id=competition_id,
            prepare_all=prepare_all,
            lite=lite,
            list_file=list_file,
            keep_raw=keep_raw,
            overwrite_checksums=overwrite_checksums,
            overwrite_leaderboard=overwrite_leaderboard,
            skip_verification=skip_verification,
        )
    except Exception as e:
        click.echo(f"Error during preparing: {e}", err=True)
        sys.exit(1)


@cli.command(
    "grade",
    help="Grade a submission covering *all* eval competitions (JSONL format).",
)
@click.option(
    "--submission",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
    required=True,
    help="JSONL submission file (see README.md).",
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, path_type=Path),
    required=True,
    help="Directory where evaluation metrics will be written.",
)
@click.option(
    "--data-dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=registry.get_data_dir(),
    show_default=True,
)
@click.pass_context
@require_init
def grade(
    ctx: click.Context,
    submission: Path,
    output_dir: Path,
    data_dir: Path,
) -> None:
    try:
        ctx.obj["registry"].set_data_dir(Path(data_dir))
        grade_api(submission, output_dir)
    except Exception as e:
        click.echo(f"Error during grading: {e}", err=True)
        sys.exit(1)


@cli.command(
    "grade-sample",
    help="Grade a *single* competition CSV submission inside the eval.",
)
@click.argument(
    "submission",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
)
@click.argument("competition_id", type=str)
@click.option(
    "--data-dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=registry.get_data_dir(),
    show_default=True,
)
@click.pass_context
def grade_sample(
    ctx: click.Context,
    submission: Path,
    competition_id: str,
    data_dir: Path,
) -> None:
    try:
        ctx.obj["registry"].set_data_dir(Path(data_dir))

        print(submission, type(submission))

        report = grade_sample_api(
            submission, competition_id,
        )
        click.echo(
            "Competition report:\n%s",
            json.dumps(report.to_dict(), indent=4)
        )
    except Exception as e:
        click.echo(f"Error during grading: {e}", err=True)
        sys.exit(1)