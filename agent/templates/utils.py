import os
import yaml

from agent.types import Task


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


def match_plan(task_dict: dict):
    """
    Match a plan task name with the task description.
    :param task_dict: the dictionary of tasks.
    :return: a task object.
    """

    tasks = load_yml('plan.yml')
    for task in tasks:
        if task_dict.get('name').lower() == task['name'].lower():
            task['description'] = task_dict.get('description')
            return Task(**task)

    return None


def get_models():
    """
    Load the models from the configuration files.
    :return: the models.
    """

    return load_yml('resource.yml').get('model')


def get_datasets():
    """
    Load the datasets from the configuration files.
    :return: the datasets.
    """

    return load_yml('resource.yml').get('dataset')
