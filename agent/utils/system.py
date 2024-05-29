import os
import re
import subprocess
from typing import Type, TypeVar

import yaml
from tinydb import TinyDB, Query
from pydantic import BaseModel
from rich.console import Console

from agent.utils import Config
from agent.types import Project
from agent.types.const import TABLE_PROJECTS

T = TypeVar('T', bound=BaseModel)
project_db = TinyDB(os.path.join(Config().home, TABLE_PROJECTS))


def preprocess_json_string(json_string):
    """
    Preprocess a JSON string to handle single quotes and other special cases.
    :param json_string: the input JSON string.
    :return: the preprocessed JSON string.
    """
    # Replace single quotes with double quotes
    json_string = re.sub(r"'", r'"', json_string)

    # Handle cases where single quotes are used inside double quotes
    json_string = re.sub(r'"\s*:\s*"', r'": "', json_string)
    json_string = re.sub(r'"\s*,\s*"', r'", "', json_string)
    json_string = re.sub(r'\[\s*"', r'["', json_string)
    json_string = re.sub(r'"\s*\]', r'"]', json_string)

    return json_string


def list_all_files(path):
    """
    Lists all files and directories under the given path if it is a directory.
    If the path is a file, returns None.

    Args:
    path (str): The file system path to check and list contents from.

    Returns:
    list of str or None: A list of file and directory names under the given path, or None if the path is a file.
    """
    if os.path.isfile(path):
        return None  # Return None if the path is a file

    file_list = []
    for root, dirs, files in os.walk(path):
        for name in files:
            file_list.append(os.path.join(root, name))
        for name in dirs:
            file_list.append(os.path.join(root, name))

    return file_list


def create_directory(dir_name: str):
    """
    Create a directory if it does not exist.
    :param dir_name: the name of the directory to create.
    :return: the directory created.
    """
    console = Console()
    cwd = os.getcwd()
    path = os.path.join(cwd, dir_name)

    try:
        os.makedirs(path, exist_ok=True)
        console.log(f"[green]Directory '{path}' created successfully. Use 'mle start' to start the project.")
    except OSError as error:
        console.log(f"[red]Creation of the directory '{path}' failed due to: {error}")
    return path


def get_directory_name(path):
    """
    Get the directory name if the path is a directory.
    :param path: the path to check.
    :return: the directory name if it's a directory, otherwise None.
    """
    if os.path.isdir(path):
        return os.path.basename(path)
    else:
        return None


def read_project_state(project_name: str):
    """
    Read the project state.
    :param project_name: the project name.
    :return: the project object.
    """
    query = Query()
    project = project_db.get(query.name == project_name)
    if project:
        return Project(**project)

    return None


def update_project_state(project: Project):
    """
    Update the project state.
    :param project: the project object.
    :return: the project object.
    """
    query = Query()
    if project_db.contains(query.name == project.name):
        project_db.update(project.dict(), query.name == project.name)
    else:
        project_db.insert(project.dict())


def list_projects():
    """
    List all the projects.
    :return: the list of projects.
    """
    return [Project(**item) for item in project_db.all()]


def extract_and_save_file(input_text):
    """
    Extracts the file name and code block from a text formatted as specified,
    then creates a local file with the file name and writes the code into it.

    Args:
    input_text (str): The text containing the file name and code block.

    Returns:
    str: The name of the file created.
    """
    console = Console()
    file_name_match = re.search(r"File Name:\s*(.*?)\s*\n+\s*Code:", input_text, re.DOTALL)
    if not file_name_match:
        console.log("File name not found in the text.")
        return None, None

    file_name = file_name_match.group(1).strip()

    project_file_path = os.path.join(Config().read()['project']['path'], file_name)
    code_match = re.search(r"```(?:[a-zA-Z0-9]+)?\n(.*?)```", input_text, re.DOTALL)
    if not code_match:
        console.log("Code block not found in the text.")
        return None, None

    code = code_match.group(1).strip()
    with open(project_file_path, 'w') as file:
        file.write(code)

    return project_file_path, code


def extract_file_name(text: str):
    """
    Extracts the file name from a given text string.

    Args:
    text (str): The text containing the file name.

    Returns:
    str: The extracted file name, or an empty string if no file name is found.
    """
    match = re.search(r'File Name: (\S+)', text)
    if match:
        return match.group(1)
    else:
        return None


def extract_code(text: str):
    """
    Extracts the code block from a given text string.

    Args:
    text (str): The text containing the code block.

    Returns:
    str: The extracted code block, or an empty string if no code block is found.
    """
    match = re.search(r'```(?:[a-zA-Z0-9]+)?\n(.*?)```', text, re.DOTALL)
    if match:
        return match.group(1)
    else:
        return None


def read_file_to_string(file_path: str):
    """
    Reads the contents of a file and returns it as a string.

    Args:
    file_path (str): The path to the file that needs to be read.

    Returns:
    str: The contents of the file as a string.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        return None


def run_command(commands):
    """
    Run multiple commands in the shell and return the outputs, errors, and exit statuses.
    :param commands: the list of input commands to run.
    :return: a list of tuples containing the output, error (if any), and exit status for each command.
    """
    results = []
    for command in commands:
        try:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

            output = ''
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                output += line
                print(line, end='')

            exit_code = process.wait()
            results.append((output, exit_code))
        except Exception as e:
            results.append((str(e), -1))


def list_dir_structure(start_path):
    """
    List all files and directories under the given path.
    :param start_path: the path to start listing from.
    :return:
    """
    return_str = ""
    for root, dirs, files in os.walk(start_path):
        level = root.replace(start_path, '').count(os.sep)
        indent = ' ' * 4 * level
        subindent = ' ' * 4 * (level + 1)
        return_str += f'{indent}{os.path.basename(root)}/\n'
        for f in files:
            return_str += f'{subindent}{f}\n'

    return return_str
