import json

from agent.types import Plan
from agent.templates import load_yml, get_models, get_datasets
from agent.utils import preprocess_json_string


def dependency_generator(plan: Plan, llm_agent):
    """
    Select the dependencies for the project plan.
    :param plan: the project plan.
    :param llm_agent: the language model agent.
    :return: the dependencies.
    """
    prompt = f"""
    You are an ML project expert that detect which dependencies the user need to install
    to meet the project plan requirements. And generate a list of shell commands to install the dependencies.
    
    - The project is written in {plan.lang}.
    - The commands should be in the form of a list.
    - The commands should be able to run in the user's environment.
    
    EXAMPLE OUTPUT in JSON FORMAT:
    
    'commands': ['python -m pip install torch', 'pip install transformers', 'apt-get install build-essential']
    
    """

    chat_history = [
        {"role": 'system', "content": prompt},
        {"role": 'user', "content": json.dumps(plan.dict())}
    ]
    resp = llm_agent.completions(chat_history, stream=False)
    results = resp.choices[0].message.content
    return json.loads(preprocess_json_string(results))


def dataset_selector(requirement: str, llm_agent):
    prompt = f"""
    You are an ML project expert provides consultation to the user based on the user's requirements.
    
    - You should select a dataset source platform from the following list.
    - You should select the dataset that can achieve the user's requirements.
    - You only return the dataset name.
    
    AVAILABLE DATASETS:
    
    {get_datasets()}
    
    OUTPUT should only a name without any punctuation.
    
    """

    chat_history = [
        {"role": 'system', "content": prompt},
        {"role": 'user', "content": requirement}
    ]
    resp = llm_agent.completions(chat_history, stream=False)
    return resp.choices[0].message.content


def model_selector(requirement: str, llm_agent):
    prompt = f"""
    You are an ML project expert provides consultation to the user based on the user's requirements.
    
    - You should select an AI model framework from the following framework list.
    - You should select the AI model framework that can achieve the user's requirements.
    - You should only return the framework name.
    
    AVAILABLE AI FRAMEWORKS:
    
    {get_models()}
    
    OUTPUT should only a name without any punctuation.
    
    """

    chat_history = [
        {"role": 'system', "content": prompt},
        {"role": 'user', "content": requirement}
    ]
    resp = llm_agent.completions(chat_history, stream=False)
    return resp.choices[0].message.content


def task_selector(requirement: str, llm_agent):
    prompt = f"""
    You are an ML project expert that determines the tasks based on the user's requirements.
    
    - You should select a task from the following task list.
    - You should not return other information except the task name.
    
    AVAILABLE TASKS:
    
    {load_yml('task.yml')}
    
    OUTPUT should only a name without any punctuation.
    
    """

    chat_history = [
        {"role": 'system', "content": prompt},
        {"role": 'user', "content": requirement}
    ]
    resp = llm_agent.completions(chat_history, stream=False)
    return resp.choices[0].message.content


def plan_generator(requirement: str, llm_agent, task: str, model_framework: str, dataset: str):
    prompt = f"""
    You are an ML project leader that generates the project plans based on the user's requirements.
    The plan includes a list of tasks that can achieve the user's requirements.
    
    You should use the tasks defined to generate a plan, select the tasks are necessary to achieve the requirements.
     and generate the proper task description based on the user's requirements, as much details as possible.
     
    Please return the plan in JSON format, without any other information.
    
    AVAILABLE TASKS:
    
    {json.dumps(load_yml('plan.yml'))}
    
    EXAMPLE OUTPUT in JSON FORMAT:
    
    "tasks": [{{'name': 'Data Pre-processing', 'description': 'Pre-process the data for the model training,
    reshape the data and do feature engineering.'}}, {{'name': 'Model Training', 'description': 'Load the
     ResNet18 model weights and train the model using the pre-processed data.'}}]
    
    """

    requirement += f"""
    \n
    
    You should generate the code base on the:
    
    - ML task: {task}
    - AI model framework: {model_framework}
    - Dataset: {dataset}
    """

    chat_history = [
        {"role": 'system', "content": prompt},
        {"role": 'user', "content": requirement}
    ]
    resp = llm_agent.completions(chat_history, stream=False)
    return json.loads(resp.choices[0].message.content)
