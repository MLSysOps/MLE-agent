import re
import os
import json
from typing import Dict, Any


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


def is_markdown_file(file_path):
    """
    Check if the file is a Markdown file.
    :param file_path: the file path
    :return: boolean
    """
    if not os.path.isfile(file_path):
        return False

    valid_extensions = ['.md', '.markdown', '.mdown', '.mkdn', '.mkd', '.mdwn', '.mdtxt', '.mdtext', '.text', '.Rmd']
    file_extension = os.path.splitext(file_path)[1].lower()

    return file_extension in valid_extensions


def read_markdown(file_path, include_links=False, include_images=False):
    """
    Read the markdown file and return the content.
    :param file_path: the file path to the .md file
    :param include_links: the flag to include the links
    :param include_images: the flag to include the images
    :return: the raw content of the markdown file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        if not include_links:
            content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)

        if not include_images:
            content = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', content)

        return content.strip()
    except FileNotFoundError:
        return f"Error: File not found at {file_path}"
    except Exception as e:
        return f"Error: An unexpected error occurred - {str(e)}"


def clean_json_string(input_string):
    """
    clean the json string
    :input_string: the input json string
    """
    cleaned = input_string.strip()
    cleaned = re.sub(r'^```\s*json?\s*', '', cleaned)
    cleaned = re.sub(r'\s*```\s*$', '', cleaned)
    parsed_json = json.loads(cleaned)
    return parsed_json
