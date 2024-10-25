import os


def read_file(file_path: str, limit: int = 2000):
    """
    Reads the contents of a file and returns it as a string.

    Args:
    file_path (str): The path to the file that needs to be read.
    limit (int, optional): Maximum number of lines to read.

    Returns:
    str: The contents of the file as a string.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            if limit <= 0:
                return file.read()
            lines = []
            for i, line in enumerate(file):
                if i >= limit:
                    break
                lines.append(line)
            return ''.join(lines)
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


def list_files(path, limit=50):
    """
    Lists files and directories under the given path if it is a directory,
    up to a specified limit.

    Args:
    path (str): The file system path to check and list contents from.
    limit (int): Maximum number of items to list. Defaults to 50.

    Returns: A string containing the list of file and directory names under
             the given path, or a message if the path is a file or if the
             number of items exceeds the limit.
    """
    if os.path.isfile(path):
        return "The given path is a file. Please provide a path of a directory."

    try:
        files = os.listdir(path)
    except PermissionError:
        return "Permission denied to access this directory."
    except FileNotFoundError:
        return "The specified directory does not exist."
    except Exception as e:
        return f"An error occurred: {str(e)}"

    total_files = len(files)

    if total_files > limit:
        files = files[:limit]
        output = "\n".join(files)
        output += f"\n\n... and {total_files - limit} more items (total of {total_files} items)"
    else:
        output = "\n".join(files)
        output += f"\n\nTotal items: {total_files}"

    return output


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
