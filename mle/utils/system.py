import os
import re
import shutil
import subprocess


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
