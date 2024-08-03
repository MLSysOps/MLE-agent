import os
import re
import yaml
import shutil

from rich.panel import Panel
from rich.prompt import Prompt
from rich.console import Console


def print_in_box(text: str, console=None, title: str = "", color: str = "white"):
    """
    Print the text in a box.
    :param text: the text to print.
    :param console: the console to print the text.
    :param title: the title of the box.
    :param color: the border color.
    :return:
    """
    if console is None:
        console = Console()

    panel = Panel(text, title=title, border_style=color, expand=False)
    console.print(panel)


def ask_text(question: str, title: str = "User", console=None) -> str:
    """
    Display a question in a panel and prompt the user for an answer.
    :param question: the question to display.
    :param title: the title of the panel.
    :param console: the console to use.
    :return: the user's answer.
    """
    if console is None:
        console = Console()

    console.print(Panel(question, title="MLE Agent", border_style="purple"))
    answer = Prompt.ask(f"Type your answer here")
    console.print(Panel(answer, title=title))
    return answer


def get_config():
    """
    Get the configuration file.
    :return: the configuration file.
    """
    config_path = os.path.join(os.getcwd(), 'project.yml')
    if not os.path.exists(config_path):
        return None

    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def write_config(value):
    """
    Write the configuration file.
    """
    config_path = os.path.join(os.getcwd(), 'project.yml')
    with open(config_path, 'w+') as file:
        yaml.dump(value, file, default_flow_style=False)


def delete_directory(path):
    """
    delete_directory: delete a directory and all its contents.

    Args:
        path: The path to the directory to be deleted.
    """
    if os.path.exists(path):
        shutil.rmtree(path)
        return True
    else:
        return False


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
