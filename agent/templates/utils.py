import os
import yaml
from pydantic import ValidationError

from agent.types import Step


def load_step(file_name: str) -> Step:
    """
    Load a step from a .yaml file.
    :param file_name: the name of the configuration file.
    :return:
    """

    dir_path = os.path.dirname(os.path.realpath(__file__))
    yml_path = os.path.join(dir_path, file_name)

    with open(yml_path, 'r') as file:
        data = yaml.safe_load(file)
    try:
        config = Step(**data)
        return config
    except ValidationError as e:
        print(f"Error in loading step file: {e}")
        raise
