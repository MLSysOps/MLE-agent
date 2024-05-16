import json
from agent.templates import load_yml, get_models, get_datasets


def dataset_selector(requirement: str, llm_agent):
    prompt = f"""
    You are an ML project expert provides consultation to the user based on the user's requirements.
    
    - You should select a dataset source platform from the following list.
    - You should select the dataset that can achieve the user's requirements.
    - You should not return other information except the dataset name.
    
    AVAILABLE DATASETS:
    
    {get_datasets()}
    
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
    - You should not return other information except the framework name.
    
    AVAILABLE AI FRAMEWORKS:
    
    {get_models()}
    
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
