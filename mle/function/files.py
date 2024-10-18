import os
from pathlib import Path


def read_file(file_path: str):
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
        return f"File not found: {file_path}"


def create_file(path, content):
    """
    Create a file with the given path and content.
    Args:
        path (str): The path to the file to create.
        content (str): The initial content to write to the file.
    """
    try:
        with open(path, 'w') as f:
            f.write(content)
        return f"File created: {path}"
    except Exception as e:
        return f"Error creating file: {str(e)}"


def write_file(path, content):
    """
    Write content to a file.
    Args:
        path (str): The path to the file to write to.
        content (str): The content to write to the file.
    """
    try:
        with open(path, 'w') as f:
            f.write(content)
        return f"Content written to file: {path}"
    except Exception as e:
        return f"Error writing to file: {str(e)}"


def list_files(path: str, max_depth=3, max_items=8, prefix_str: str = "") -> str:
    """
    Lists all files and directories under the given path if it is a directory.
    If the path is a file, returns None.
    Args:
        path (str): The root directory path to list.
        max_depth (int): Maximum depth to traverse the directory structure.
        max_items (int): Maximum number of items to display in each directory.
    """
    def format_size(size: int) -> str:
        """Format the file size in a human-readable way."""
        return f"{size:,} bytes"

    def get_lines_count(file_path: str) -> int:
        """Get the number of lines in a text file."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)

    def list_directories(path: str, max_depth=4, max_items=8, prefix_str: str = "") -> str:
        """
        Generate a text structure representing the directory contents.
        """
        if max_depth <= 0:
            return ""

        directories, files = [], []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                directories.append(item)
            else:
                files.append(item)

        items_info = []

        # Process directories
        for i, directory in enumerate(directories[:max_items]):
            dir_path = os.path.join(path, directory)
            is_last = i + 1 == len(directories) and len(files) == 0
            sub_items = list_directories(
                dir_path, max_depth - 1, max_items,
                prefix_str + ("    " if is_last else "│   "),
            )

            if is_last:
                dir_info = f"{prefix_str}└── {directory}/ "
            else:
                dir_info = f"{prefix_str}│── {directory}/ "

            items_info.append(
                f"{dir_info} "
                f"({len([d for d in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, d))])} directories"
                f", {len([f for f in os.listdir(dir_path) if not os.path.isdir(os.path.join(dir_path, f))])} files)"
                f"{os.linesep + sub_items if sub_items else ''}"
            )

        if len(directories) > max_items:
            if len(files) == 0:
                items_info.append(f"{prefix_str}└── .../ (remaining: {len(directories) - max_items} directories)")
            else:
                items_info.append(f"{prefix_str}│── .../ (remaining: {len(directories) - max_items} directories)")

        # Process files
        for i, file in enumerate(files[:max_items]):
            file_path = os.path.join(path, file)
            is_last = i + 1 == len(files)

            if is_last:
                file_info = f"{prefix_str}└── {file} "
            else:
                file_info = f"{prefix_str}│── {file} "

            if file.endswith(('.zip', '.tar.gz', '.gz')):
                file_info += f"({format_size(os.path.getsize(file_path))})"
            elif file.endswith(('.txt', '.md', '.json', '.yaml')):
                file_info += f"({get_lines_count(file_path)} lines)"
            else:
                file_info += f"({format_size(os.path.getsize(file_path))})"

            items_info.append(file_info)

        if len(files) > max_items:
            items_info.append(f"{prefix_str}└── ... (remaining: {len(files) - max_items} files)")

        return '\n'.join(items_info)

    if os.path.isfile(path):
        return "The given path is a file. Please provide a path of a directory."

    return f"{Path(path).absolute()}\n" + list_directories(path, max_depth - 1, max_items)


def create_directory(path: str):
    """
    Create a directory if it does not exist.
    Args:
        path (str): The path to the directory to create.
    """
    try:
        os.makedirs(path, exist_ok=True)
        return f"Directory '{path}' created successfully."
    except OSError as error:
        return f"Creation of the directory '{path}' failed due to: {error}"
