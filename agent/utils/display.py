import os
from prettytable import PrettyTable
from colorama import Fore, Style, init

init(autoreset=True)


def get_terminal_size():
    """
    Get the width of the terminal

    Returns:
    int: The width of the terminal
    """
    try:
        columns = os.get_terminal_size().columns
    except OSError:
        columns = 120  # default width if terminal size cannot be determined
    return columns


def split_text(text, max_width=80, max_lines=5):
    """
    Split text based on maximum width and maximum lines

    Args:
    text (str): The text to be split
    max_width (int, optional): Maximum width per line. Defaults to 80.
    max_lines (int, optional): Maximum number of lines. Defaults to 5.

    Returns:
    list: List of split text
    """
    words = text.split()
    lines = []
    current_line = words[0]

    for word in words[1:]:
        if len(current_line) + len(word) < max_width:
            current_line += " " + word
        else:
            if len(lines) >= max_lines - 1:
                current_line += "..."
                break
            lines.append(current_line)
            current_line = word
    lines.append(current_line)
    return lines


def generate_one_plan_card_ascii(
        step: int,
        name: str,
        resources: list[str],
        description: str,
        max_width: int = 80,
        require_arrow: bool = True,
):
    """
    Generate ASCII art for a single plan card

    Args:
        step (int): The step number
        name (str): The name of the task
        resources (list): List of resources
        description (str): Description of the task
        max_width (int, optional): Maximum width. Defaults to 80.
        require_arrow (bool, optional): Whether an arrow is required. Defaults to True.

    Returns:
        str: ASCII art string
    """
    max_width = min(get_terminal_size() // 2 - 10, max_width)
    table = PrettyTable()
    table.title = (
            Fore.YELLOW
            + Style.BRIGHT
            + f"Task {step + 1}: {name}"
            + Style.RESET_ALL
    )
    table.field_names = [
        Fore.BLUE + "Resources" + Style.RESET_ALL,
        Fore.GREEN + ", ".join(resources) + Style.RESET_ALL,
    ]
    table.add_rows(
        [
            [
                (Fore.BLUE + "Description" + Style.RESET_ALL) if i == 0 else "",
                Fore.GREEN + s + Style.RESET_ALL,
            ]
            for i, s in enumerate(split_text(description, max_width))
        ]
    )
    table.hrules = False
    table_string = table.get_string()

    terminal_width = get_terminal_size()
    table_width = len(table_string.split("\n")[0])
    table_padding = (
        (terminal_width - table_width) // 2 if terminal_width > table_width else 0
    )

    strs = ""
    for line in table_string.split("\n"):
        strs += " " * table_padding + line + "\n"

    if require_arrow:
        strs += " " * (terminal_width // 2) + Fore.MAGENTA + "|" + Style.RESET_ALL + "\n"
        strs += " " * (terminal_width // 2) + Fore.MAGENTA + "V" + Style.RESET_ALL + "\n"

    return strs


def generate_plan_card_ascii(task_dicts):
    """
    Generate ASCII art for plan cards

    Args:
        task_dicts (dict): Dictionary of tasks

    Returns:
        str: ASCII art string
    """
    strs = ""
    for i, plan in enumerate(task_dicts["tasks"]):
        strs += generate_one_plan_card_ascii(step=i, require_arrow=i != len(task_dicts["tasks"]) - 1, **plan)
    return strs
