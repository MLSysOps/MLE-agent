import os
import yaml


def load_yml(file_name: str):
    """
    Load a step from a .yaml file.
    :param file_name: the name of the configuration file.
    :return:
    """

    dir_path = os.path.dirname(os.path.realpath(__file__))
    yml_path = os.path.join(dir_path, file_name)

    with open(yml_path, 'r') as file:
        data = yaml.safe_load(file)

    return data