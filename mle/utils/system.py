import os
import re
import yaml
import shutil
import questionary

from rich.text import Text
from rich.panel import Panel
from rich.layout import Layout
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


def text_box(text: str, console=None, title: str = "You"):
    """
    Print the text in a chat box.
    :param text: the text to print.
    :param console: the console to print the text.
    :param title: the title of the box.
    :return: the user input.
    """
    layout = Layout()
    question_text = Text("Type something:", style="bold white")
    question_panel = Panel(question_text, title=title, subtitle="Type 'exit' or 'quit' to stop", expand=False)

    layout.split(Layout(question_panel, name="question"))
    console.print(layout)

    user_input = questionary.text(text).ask()

    # Display the user's input
    answer_text = Text(f"You typed: {user_input}", style="bold blue")
    answer_panel = Panel(answer_text, title="Response", expand=False)

    layout.split(
        Layout(question_panel, name="question"),
        Layout(answer_panel, name="answer")
    )

    console.print(layout)
    return user_input


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
