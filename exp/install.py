#!/usr/bin/env python3
"""
Author: Li Yuanming
Email: yuanmingleee@gmail.com
Date: Jul 11, 2025

grab_mle_experiments.py
-----------------------
Download openai/mle-bench's `experiments/` directory (with Git-LFS files) and
copy it into the installed `mlebench` package’s folder inside site-packages.

Run:  python grab_mle_experiments.py
"""

import importlib.util
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_URL = "https://github.com/openai/mle-bench.git"
BRANCH = "main"
SUBDIR = "experiments"


def run(cmd, cwd=None):
    """Run `cmd` (list of str). Raise if non-zero."""
    print("→", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def find_site_pkg_dir():
    spec = importlib.util.find_spec("mlebench")
    if spec is None or not spec.origin:
        sys.exit("❌  The `mlebench` package is not installed in this interpreter.")
    return Path(spec.origin).parents[1]  # …/site-packages


def install(upgrade=False):
    dest_pkg_dir = find_site_pkg_dir()
    dest_exp_dir = dest_pkg_dir / SUBDIR
    print(f"📦  mlebench package is at: {dest_pkg_dir}")

    # Wipe any existing experiments/ copy
    if dest_exp_dir.exists():
        print("🧹  Removing old experiments/ folder …")
        shutil.rmtree(dest_exp_dir)

    # Clone repo sparsely into a temp dir
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        repo_dir = tmp / "mle-bench"
        print(f"⬇️  Cloning {REPO_URL} → {repo_dir}")
        run(["git", "clone", "--depth=1", REPO_URL, str(repo_dir)])

        # Sparse-checkout just the experiments folder
        # run(["git", "sparse-checkout", "init", "--cone"], cwd=repo_dir)
        # run(["git", "sparse-checkout", "set", SUBDIR], cwd=repo_dir)
        # run(["git", "checkout", BRANCH], cwd=repo_dir)

        # Pull the large-file objects
        run(["git", "lfs", "pull"], cwd=repo_dir)

        src_exp_dir = repo_dir / SUBDIR
        if not src_exp_dir.is_dir():
            sys.exit("❌  experiments/ folder was not found in the clone.")

        # Copy into site-packages
        print(f"🚚  Copying {src_exp_dir} → {dest_exp_dir}")
        shutil.copytree(src_exp_dir, dest_exp_dir)

    # Quick sanity check: make sure at least one non-pointer file exists
    some_file = next(dest_exp_dir.rglob("*"), None)
    if some_file and some_file.stat().st_size > 150:  # LFS pointers are ~130 B
        print(f"✅  Done! Sample file copied: {some_file.relative_to(dest_pkg_dir)}")
    else:
        print("⚠️  Warning: files might still be Git-LFS pointers; check your git-lfs setup.")


if __name__ == "__main__":
    try:
        install()
    except subprocess.CalledProcessError as e:
        sys.exit(f"\n❌  Command failed: {e.cmd}\n    (exit code {e.returncode})")
