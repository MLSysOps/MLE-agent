#!/usr/bin/env python3
"""
Author: Li Yuanming
Email: yuanmingleee@gmail.com
Date: Jul 12, 2025
"""
import sys
from pathlib import Path

from mlebench.data import download_and_prepare_dataset
from mlebench.grade import grade_csv, grade_jsonl
from mlebench.grade_helpers import CompetitionReport
from mlebench.registry import registry


def prepare(
    competition_id: str | None = None,
    prepare_all: bool = False,
    lite: bool = False,
    list_file: Path | None = None,
    keep_raw: bool = False,
    overwrite_checksums: bool = False,
    overwrite_leaderboard: bool = False,
    skip_verification: bool = False,
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
        # resolve list of competitions to process
        if lite:
            comps = [registry.get_competition(cid) for cid in registry.get_lite_competition_ids()]
        elif prepare_all:
            comps = [registry.get_competition(cid) for cid in registry.list_competition_ids()]
        elif list_file:
            cids = list_file.read_text().splitlines()
            comps = [registry.get_competition(cid) for cid in cids]
        elif competition_id:
            comps = [registry.get_competition(competition_id)]
        else:
            raise ValueError(
                "One of `lite`, `all`, `list`, or `competition_id` is required."
            )

        for comp in comps:
            download_and_prepare_dataset(
                competition=comp,
                keep_raw=keep_raw,
                overwrite_checksums=overwrite_checksums,
                overwrite_leaderboard=overwrite_leaderboard,
                skip_verification=skip_verification,
            )
    finally:
        if _restore_patch:
            _restore_patch()


def grade(
    submission: Path,
    output_dir: Path,
) -> None:
    grade_jsonl(Path(submission), Path(output_dir), registry)


def grade_sample(
    submission: Path,
    competition_id: str,
) -> CompetitionReport:
    comp = registry.get_competition(competition_id)
    return grade_csv(Path(submission), comp)
