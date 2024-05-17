import json

from agent.types import Plan
from agent.templates import load_yml
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
    
    - You should choose a dataset that can achieve the user's requirements.
    - You only return the dataset name.
    - Noted: it is the name of the dataset, not the platform hosts the dataset.
    
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
    
    - You should choose an AI model framework that can achieve the user's requirements.
    - You should only return the framework name.
    - Note: it if the model architecture name, not the framework builds the model.
    
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

    resp = llm_agent.completions([{"role": 'system', "content": prompt},
                                  {"role": 'user', "content": requirement}], stream=False)
    return resp.choices[0].message.content


def description_generator(requirement: str, task_list, llm_agent):
    sys_prompt = f"""
    You are an ML engineer that generates a task guide based on the task name,
     resources, and the user's requirements.
    
    - You should generate the task guide description based on the user's requirements.
    - You are welcome to add as more details as possible, but don't add irrelevant information under the task.
    - You should add an attribute 'description' to the task.
    
    EXAMPLE OUTPUT in JSON FORMAT:
    
    "tasks": [
    {{'name': 'Data Pre-processing', 'resources': [],
     'description': 'This task is first to preprocess the data. Second to ...'}},
    {{'name': 'Model Training', 'resources': 'PyTorch',
     'description': 'This task is to train the model using PyTorch, ...'}},
    {{'name': 'Model Deployment', 'resources': ['Flask'],
     'description': 'This task is to deploy the model using Flask, ...'}}
    ]
    
    """

    user_prompt = f"""
    Overall Requirements: {requirement}
    Tasks: {task_list}
    """

    chat_history = [
        {"role": 'system', "content": sys_prompt},
        {"role": 'user', "content": user_prompt}
    ]
    resp = llm_agent.completions(chat_history, stream=False)
    return json.loads(resp.choices[0].message.content)


def plan_generator(
        requirement: str,
        llm_agent,
        ml_model_arch: str,
        ml_dataset_name: str,
        ml_task_name: str
):
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

    prompt = f"""
    You are an ML project leader that generates the project plans based on the user's requirements.
    The plan includes a list of tasks that can achieve the user's requirements.
    
    - You use the tasks only from the following task list.
    - You should select as less as possible resources to achieve the requirements.
    - Please return the plan in JSON format, without any other information.
    
    AVAILABLE TASKS AND RESOURCES:
    
    {json.dumps({"tasks": task_list})}
    
    EXAMPLE OUTPUT in JSON FORMAT:
    
    "tasks": [
    {{'name': 'Data Collection', 'resources': [HuggingFace Dataset]}},
     {{'name': 'Data Pre-processing', 'resources': []}},
     {{'name': 'Model Training', 'resources': 'PyTorch'}},
     {{'name': 'Model Deployment', 'resources': ['Flask']}}
    ]
    
    """

    requirement += f"""
    \n
    
    You should generate the plan base on the:
    
    - ML task kind: {ml_task_name}
    - AI model architecture: {ml_model_arch}
    - Dataset: {ml_dataset_name}
    """

    chat_history = [
        {"role": 'system', "content": prompt},
        {"role": 'user', "content": requirement}
    ]
    resp = llm_agent.completions(chat_history, stream=False)
    target_tasks = resp.choices[0].message.content

    # generate the completed plan with detailed description
    return description_generator(requirement, target_tasks, llm_agent)
