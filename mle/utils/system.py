import os
import re
import yaml
import base64
import shutil
import requests
from typing import Dict, Any, Optional
from rich.panel import Panel
from rich.prompt import Prompt
from rich.console import Console


def dict_to_markdown(data: Dict[str, Any], file_path: str) -> None:
    """
    Write a dictionary to a markdown file.
    :param data: the dictionary to write.
    :param file_path: the file path to write the dictionary to.
    :return:
    """

    def write_item(k, v, indent_level=0):
        if isinstance(v, dict):
            md_file.write(f"{'##' * (indent_level + 1)} {k}\n")
            for sub_key, sub_value in v.items():
                write_item(sub_key, sub_value, indent_level + 1)
        elif isinstance(v, list):
            md_file.write(f"{'##' * (indent_level + 1)} {k}\n")
            for item in v:
                md_file.write(f"{'  ' * indent_level}- {item}\n")
        else:
            md_file.write(f"{'##' * (indent_level + 1)} {k}\n")
            md_file.write(f"{'  ' * indent_level}{v}\n")

    with open(file_path, 'w') as md_file:
        for key, value in data.items():
            write_item(key, value)
            md_file.write("\n")


def print_in_box(text: str, console: Optional[Console] = None, title: str = "", color: str = "white") -> None:
    """
    Print the text in a box.
    :param text: the text to print.
    :param console: the console to print the text.
    :param title: the title of the box.
    :param color: the border color.
    :return:
    """
    console = console or Console()

    panel = Panel(text, title=title, border_style=color, expand=False)
    console.print(panel)


def ask_text(question: str, title: str = "User", console: Optional[Console] = None) -> str:
    """
    Display a question in a panel and prompt the user for an answer.
    :param question: the question to display.
    :param title: the title of the panel.
    :param console: the console to use.
    :return: the user's answer.
    """
    console = console or Console()

    console.print(Panel(question, title="MLE Agent", border_style="purple"))
    answer = Prompt.ask(f"Type your answer here")
    console.print(Panel(answer, title=title))
    return answer


def check_config(console: Optional[Console] = None):
    """
    check_config: check if the configuration file exists.
    :return: True if the configuration file exists, False otherwise.
    """""
    console = console or Console()
    current_work_dir = os.getcwd()

    config_dir = os.path.join(current_work_dir, '.mle')
    config_path = os.path.join(config_dir, 'project.yml')

    # move the old config file to the new path for compatibility (delete in future)
    old_config_path = os.path.join(os.getcwd(), 'project.yml')
    if os.path.exists(old_config_path):
        os.makedirs(config_dir, exist_ok=True)
        shutil.move(old_config_path, config_path)

    if not os.path.exists(config_path):
        console.log("Configuration file not found. Please run 'mle new' first.")
        return False

    with open(config_path, 'r') as file:
        data = yaml.safe_load(file)
        if data.get('search_key'):
            os.environ["SEARCH_API_KEY"] = data.get('search_key')

    return True


def get_config() -> Optional[Dict[str, Any]]:
    """
    Get the configuration file.
    :return: the configuration file.
    """
    config_dir = os.path.join(os.getcwd(), '.mle')
    config_path = os.path.join(config_dir, 'project.yml')
    if not os.path.exists(config_path):
        return None

    with open(config_path, 'r') as file:
        return yaml.safe_load(file)


def write_config(value: Dict[str, Any]) -> None:
    """
    Write the configuration file.
    """
    config_dir = os.path.join(os.getcwd(), '.mle')
    config_path = os.path.join(config_dir, 'project.yml')
    os.makedirs(config_dir, exist_ok=True)
    with open(config_path, 'w') as file:
        yaml.dump(value, file, default_flow_style=False)


def delete_directory(path: str) -> bool:
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


def get_directory_name(path: str) -> Optional[str]:
    """
    Get the directory name if the path is a directory.
    :param path: the path to check.
    :return: the directory name if it's a directory, otherwise None.
    """
    if os.path.isdir(path):
        return os.path.basename(path)
    else:
        return None


def extract_file_name(text: str) -> Optional[str]:
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


def list_dir_structure(start_path: str) -> str:
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


def load_file(filepath: str, base64_decode: bool = False) -> str:
    """
    Load content from a file or URL.
    :param filepath: The path to the file or a URL.
    :param base64_decode: Whether to decode the content from Base64 format.
    :return: The content of the file or URL as a decoded text string.
    """
    if filepath.startswith('http://') or filepath.startswith('https://'):
        response = requests.get(filepath)
        response.raise_for_status()
        text = response.text
    else:
        filepath = filepath.replace("file://", "")
        with open(filepath, 'r', encoding='utf-8') as file:
            text = file.read()

    if base64_decode:
        text = base64.b64decode(text).decode('utf-8')
    return text
