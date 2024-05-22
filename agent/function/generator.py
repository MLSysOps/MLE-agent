import json

from agent.types import Plan
from agent.templates import load_yml
from agent.utils import preprocess_json_string
from agent.prompt import (
    pmpt_chain_dependency,
    pmpt_dataset_selection,
    pmpt_model_selection,
    pmpt_task_selection,
    pmpt_dataset_detector,
    pmpt_task_desc,
    pmpt_plan
)


def dependency_generator(plan: Plan, llm_agent):
    """
    Select the dependencies for the project plan.
    :param plan: the project plan.
    :param llm_agent: the language model agent.
    :return: the dependencies.
    """
    chat_history = [
        {"role": 'system', "content": pmpt_chain_dependency(plan.lang)},
        {"role": 'user', "content": json.dumps(plan.dict())}
    ]
    resp = llm_agent.completions(chat_history, stream=False)
    results = resp.choices[0].message.content
    return json.loads(preprocess_json_string(results))


def datasource_detector(requirement: str, llm_agent):
    """
    Detect the dataset based on the user's requirements.
    :param requirement: the user's requirements.
    :param llm_agent: the language model agent.
    :return: the dataset name.
    """
    chat_history = [
        {"role": 'system', "content": pmpt_dataset_detector()},
        {"role": 'user', "content": requirement}
    ]
    resp = llm_agent.completions(chat_history, stream=False)
    return resp.choices[0].message.content


def dataset_selector(requirement: str, llm_agent):
    """
    Select the dataset based on the user's requirements.
    :param requirement: the user's requirements.
    :param llm_agent: the language model agent.
    :return: the dataset name.
    """
    chat_history = [
        {"role": 'system', "content": pmpt_dataset_selection()},
        {"role": 'user', "content": requirement}
    ]
    resp = llm_agent.completions(chat_history, stream=False)
    return resp.choices[0].message.content


def model_selector(requirement: str, llm_agent):
    """
    Select the model based on the user's requirements.
    :param requirement: the user's requirements.
    :param llm_agent: the language model agent.
    :return: the model name.
    """
    chat_history = [
        {"role": 'system', "content": pmpt_model_selection()},
        {"role": 'user', "content": requirement}
    ]
    resp = llm_agent.completions(chat_history, stream=False)
    return resp.choices[0].message.content


def task_selector(requirement: str, llm_agent):
    """
    Select the task based on the user's requirements.
    :param requirement: the user's requirements.
    :param llm_agent: the language model agent.
    :return: the task name.
    """
    resp = llm_agent.completions([
        {"role": 'system', "content": pmpt_task_selection()},
        {"role": 'user', "content": requirement}
    ], stream=False)
    return resp.choices[0].message.content


def description_generator(requirement: str, task_list, llm_agent):
    """
    Generate the detailed description of the plan.
    :param requirement: the user's requirements.
    :param task_list: the selected task list.
    :param llm_agent: the language model agent.
    :return: the detailed description of the plan.
    """
    user_prompt = f"""
    Overall Requirements: {requirement}
    Tasks: {task_list}
    """

    chat_history = [
        {"role": 'system', "content": pmpt_task_desc()},
        {"role": 'user', "content": user_prompt}
    ]
    resp = llm_agent.completions(chat_history, stream=False)
    return json.loads(resp.choices[0].message.content)


def plan_generator(
        requirement: str,
        llm_agent,
        ml_model_arch: str,
        ml_dataset: str,
        ml_task_name: str
):
    """
    Generate the project plan based on the user's requirements.
    :param requirement: the user's requirements.
    :param llm_agent: the language model agent.
    :param ml_model_arch: the AI model architecture.
    :param ml_dataset: the dataset prompt.
    :param ml_task_name: the ML task name.
    :return: the project plan.
    """
    task_list = []
    for task in load_yml('plan.yml'):
        if task.get('resources'):
            task_list.append(
                {
                    'name': task['name'],
                    'resources': [r['name'] for r in task.get('resources')]
                }
            )
        else:
            task_list.append(
                {
                    'name': task['name'],
                    'resources': []
                }
            )

    requirement += f"""
    \n
    
    You should generate the plan base on the:
    
    - ML task kind: {ml_task_name}
    - AI model architecture: {ml_model_arch}
    - Dataset: {ml_dataset}
    """

    chat_history = [
        {"role": 'system', "content": pmpt_plan(json.dumps(task_list))},
        {"role": 'user', "content": requirement}
    ]
    resp = llm_agent.completions(chat_history, stream=False)
    target_tasks = resp.choices[0].message.content

    # generate the completed plan with detailed description
    return description_generator(requirement, target_tasks, llm_agent)
