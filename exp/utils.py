#!/usr/bin/env python3
"""
Author: Li Yuanming
Email: yuanmingleee@gmail.com
Date: Jul 12, 2025
"""
import logging
import mimetypes
import os
import random
import venv
import zipfile
from collections import defaultdict
from io import StringIO
from pathlib import Path

import pandas as pd
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool as tool_wrapper


def get_logger(name: str = __name__, level: int = logging.INFO) -> logging.Logger:
    """
    Get a logger with the specified name and level.

    Args:
        name (str): The name of the logger.
        level (int): The logging level (default is INFO).

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    formatter = logging.Formatter('[%(asctime)s] [%(name)s:%(lineno)d] - %(levelname)s - %(message)s')

    # Remove all handlers (avoids duplicates from earlier logging setup)
    while logger.hasHandlers():
        logger.removeHandler(logger.handlers[0])

    ch = logging.StreamHandler()
    ch.setLevel(level)

    ch.setFormatter(formatter)

    logger.addHandler(ch)

    logger.propagate = False

    return logger


def get_vllm_with_tools(model, tools, **kwargs):
    """
    Call the LLM model with tools.

    Args:
        model: The LLM model instance.
        tools (list): List of tool functions to be used by the model.
        **kwargs: Additional parameters for the model query.

    Returns:
        An instance of the LLM model with the specified tools bound to it.
    """
    llm = init_chat_model(
        model=model,
        model_provider="openai",
        openai_api_key="EMPTY",
        openai_api_base="http://localhost:8000/v1",
        **kwargs
    )
    return llm.bind_tools(
        tools=[tool_wrapper(tool) for tool in tools],
    )


def build_tree_dict(path: Path, max_files: int = 10) -> list:
    tree = dict()
    if path.is_dir():
        entries = sorted(path.iterdir())
        files = [e for e in entries if e.is_file()]
        dirs = [e for e in entries if e.is_dir()]

        # Sample files up to max_files
        sampled_files = random.sample(files, min(len(files), max_files))
        for file in sampled_files:
            # Use the file name as the key and None as the value
            tree[file.name] = read_file_content(file)
        # Add a note if there are more files
        if len(files) > max_files:
            tree["..."] = f"(total {len(files)} files)"
        for d in dirs:
            tree[d.name] = build_tree_dict(d, max_files)  # Recurse for dirs

    return tree


def read_file_content(file_path: Path) -> str | None:
    """
    Read the content of a file.

    Args:
        file_path (Path): The path to the file.

    Returns:
        str: The content of the file.
    """
    if not file_path.is_file():
        return None

    mime_type, _ = mimetypes.guess_type(file_path.as_posix())
    num_lines = 10  # Number of lines to read for preview

    # CSV File
    if file_path.suffix == ".csv":
        try:
            df = pd.read_csv(file_path, nrows=num_lines)
            return f"Preview:\n{df.to_string(index=False)}"
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            return None

    # Markdown File
    elif file_path.suffix == ".md":
        try:
            with file_path.open('r', encoding='utf-8') as f:
                lines = [next(f) for _ in range(num_lines)]
            return f"Preview:\n{''.join(lines)}"
        except Exception as e:
            print(f"Error reading markdown: {e}")
            return None

    # Image File — Skip
    elif mime_type and mime_type.startswith("image/"):
        return None

    # Zip File
    elif file_path.suffix == ".zip":
        try:
            with zipfile.ZipFile(file_path, 'r') as zipf:
                return f"ZIP File Structure:\n{format_zip_tree(zipf)}"
        except Exception as e:
            print(f"Error reading zip file: {e}")
            return None

    # Unknown/unsupported, read a few lines if plain text, or return empty
    # if the file is binary
    else:
        try:
            with file_path.open('r', encoding='utf-8') as f:
                lines = [next(f) for _ in range(num_lines)]
            return f"Preview:\n{''.join(lines)}"
        except Exception as e:
            print(f"Error reading file: {e}")
            return None


def format_zip_tree(zipf: zipfile.ZipFile, max_files_per_folder: int = 10) -> str:
    """
    Build a string representation of the folder tree in a zip file.

    Args:
        zipf (zipfile.ZipFile): The opened zip file.
        max_files_per_folder (int): Max number of files to sample per folder.

    Returns:
        str: The tree structure as a string.
    """
    tree = defaultdict(list)

    # Group files by directory
    for name in zipf.namelist():
        parts = name.strip("/").split("/")
        if not parts:
            continue
        *dirs, file = parts
        folder = "/".join(dirs)
        tree[folder].append(file)

    # Recursive tree printer
    def build_tree(current_path: str, indent: str = "") -> str:
        output = StringIO()
        entries = tree.get(current_path, [])
        subfolders = sorted(
            {name for name in tree if
             name.startswith(current_path + "/" if current_path else "") and "/" in name[len(current_path):].strip("/")}
        )
        files = [f for f in entries if f]

        # Show sampled files
        if files:
            sampled = random.sample(files, min(len(files), max_files_per_folder))
            for fname in sorted(sampled):
                output.write(f"{indent}- {fname}\n")
            if len(files) > max_files_per_folder:
                output.write(f"{indent}- ... ({len(files)} files total)\n")

        # Recurse into subfolders
        for sub in subfolders:
            subname = sub[len(current_path):].strip("/") if current_path else sub
            output.write(f"{indent}+ {subname}/\n")
            output.write(build_tree(sub, indent + "  "))

        return output.getvalue()

    return build_tree('')


def find_existing_venv(cwd='.'):
    """Check for common virtual environment folders in the directory."""
    common_venv_dirs = ['venv', '.venv', 'env', '.env']
    for name in common_venv_dirs:
        candidate = (Path(cwd) / name).absolute()
        pyvenv_cfg = candidate / 'pyvenv.cfg'
        python_executable = candidate / 'bin' / 'python' if os.name != 'nt' else candidate / 'Scripts' / 'python.exe'
        if candidate.is_dir() and pyvenv_cfg.exists() and pyvenv_cfg.is_file():
            return python_executable if python_executable.exists() else None
    return None


def create_virtualenv(cwd='.', path='.venv'):
    """Create a new virtual environment at the given path."""
    venv_path = Path(cwd) / path
    builder = venv.EnvBuilder(with_pip=True)
    builder.create(venv_path)
    return venv_path.absolute() / 'bin' / 'python' if os.name != 'nt' else venv_path / 'Scripts' / 'python.exe'
