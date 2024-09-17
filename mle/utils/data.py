import re
import json


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
