import re
import os
import json


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
