import os
import yaml
from rich.console import Console

from agent.types import ProjectState
from agent.const import CONFIG_PROJECT_FILE


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
        console.log(f"[green]Directory '{path}' created successfully.")
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


def read_project_state(config_path: str = None):
    """
    Read the project state.
    :return: the project state.
    """
    console = Console()
    if not config_path:
        config_path = os.path.join(os.getcwd(), CONFIG_PROJECT_FILE)

    if not os.path.exists(config_path):
        console.log(f"[red]The file {config_path} does not exist.")
        return None

    try:
        with open(config_path, 'r') as file:
            data = yaml.safe_load(file)
            return ProjectState(**data)
    except FileNotFoundError:
        console.log(f"[red]The file {config_path} does not exist.")
        return None
    except yaml.YAMLError as error:
        console.log(f"[red]Error parsing YAML file: {error}")
        return None
    except Exception as error:
        console.log(f"[red]An error occurred: {error}")
        return None


def update_project_state(project_path: str, content_dict: dict = None):
    """
    Update the project state.
    :param project_path: the path of the project.
    :param content_dict: the content dictionary to update.
    """
    console = Console()
    file_path = os.path.join(project_path, CONFIG_PROJECT_FILE)

    try:
        with open(file_path, 'w') as file:
            yaml.dump(content_dict, file)
        console.log(f"[green]File '{file_path}' updated successfully.")
    except IOError as error:
        console.log(f"[red]Updating the file '{file_path}' failed due to: {error}")
