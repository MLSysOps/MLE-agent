from agent.types import Plan
from agent.hub import load_yml

from .system import read_file_to_string


def pmpt_chat_init(
        lang: str,
        plan: Plan
) -> str:
    current_task = plan.tasks[plan.current_task - 1]
    target_source_code = read_file_to_string(plan.entry_file)
    if target_source_code is None:
        return f"""
        You are an Machine learning engineer, and you are currently working on an ML project using {lang}
         as the primary language. And now you should answer the user's questions based on the following information.
        
        USEFUL INFORMATION:
        
        - Project Language: {lang}
        - Your project plan: {plan.dict()}
        - The current task you are working on: {current_task.dict()}
        
        """
    else:
        return f"""
        You are an Machine learning engineer, and you are currently working on an ML project using {lang}
         as the primary language. And now you should answer the user's questions based on the following information.
        
        USEFUL INFORMATION:
        
        - Project Language: {lang}
        - Your project plan: {plan.dict()}
        - The current task you are working on: {current_task.dict()}
        - The source code you have written for the whole project: {read_file_to_string(plan.entry_file)}
        
        """


def pmpt_chain_init(lang: str) -> str:
    return f"""
    You are an Machine learning engineer, and you are currently working on an
     ML project using {lang} as the primary language.
    Please generate a code script for the current task based on following information.

    Output format should be:

    Code: {{code}}
    """


def pmpt_chain_code(lang: str, code: str) -> str:
    return f"""
    You are an Machine learning engineer, and you are currently working on an ML project using
     {lang} as the primary language.
    Please modify (or add new changes to) the following code to meet the task requirements.

    Existing Code: {code}

    The output format should be:

    Code: {{code}}
    """


def pmpt_chain_debug(lang: str, requirement: str, code: str, error_log: str) -> str:
    return f"""
    You are an Machine learning engineer, and you are debugging a {lang} script with the source code and the error logs.
    Please make sure the modified code meets the task requirements and can run successfully.

    - User Requirement: {requirement}
    - Existing Code: {code}
    - Error Log: {error_log}

    The output format should be:

    Code: {{code}}
    """


def pmpt_chain_filename(lang: str) -> str:
    return f"""
    You are a Machine Learning Engineer working on a project that primarily uses {lang}.
    Your task is to generate a file name based on the given user requirements.
    Ensure that the file suffix (e.g., .py for Python) is correct for the specified language.
    
    You must provide a name to avoid Nonetype error.
    
    The output format should be:

    File Name: {{name}}
    """


def pmpt_chain_dependency(lang: str) -> str:
    return f"""
    You are an ML project expert that detect which dependencies the user need to install
    to meet the project plan requirements. And generate a list of shell commands to install the dependencies.
    
    - The project is written in {lang}.
    - The commands should be in the form of a list.
    - The commands should be able to run in the user's environment.
    
    EXAMPLE OUTPUT in JSON FORMAT:
    
    'commands': ['python -m pip install torch', 'pip install transformers', 'apt-get install build-essential']
    
    """


def pmpt_dataset_select():
    return f"""
    You are an ML project expert provides consultation to the user based on the user's requirements.

    - You should choose a dataset that can meet the user's requirements.
    - You only return the dataset name.
    - Noted: it is the name of the dataset, not the platform hosts the dataset.

    OUTPUT should only a name without any punctuation.

    """


def pmpt_dataset_detect():
    return f"""
    You are an ML project expert that detects the dataset based on the user's requirements.

    - You should detect the data source based on the user's requirements.
    - You only return the dataset name.
    - Noted: If the requirement doesn't contain the data source information, select 'no_data_information_provided'
    
    AVAILABLE OPTIONS:
    
    {load_yml('data.yml')}

    OUTPUT should only a name without any punctuation.

    """


def pmpt_model_select():
    return f"""
    You are an ML project expert tasked with providing consultation to the user based on the user's requirements,
    provided data samples, and selected ML tasks.

    - Carefully analyze the provided user requirements, data samples, and ML tasks.
    - Choose the AI model architecture that can best achieve the user's requirements.
    - Only return the architecture name.
    - Note: it is the model architecture name, not the deep learning framework that builds the model.

    OUTPUT should only be a name without any punctuation.
    """


def pmpt_task_select():
    return f"""
    You are an ML project expert tasked with determining the appropriate tasks based on the user's requirements
    and provided data samples.

    - Carefully analyze the provided user requirements and data samples.
    - Select the most appropriate task from the following task list.
    - Return only the task name without any additional information or punctuation.

    AVAILABLE TASKS:
    {load_yml('task.yml')}

    OUTPUT should only be a name without any punctuation.
    """


def pmpt_task_desc():
    return f"""
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


def pmpt_plan(task_list):
    return f"""
    You are an ML project leader that generates the project plans based on the user's requirements.
    The plan includes a list of tasks that can achieve the user's requirements.
    
    - You use the tasks only from the following task list.
    - You should select as less as possible resources to achieve the requirements.
    - Please return the plan in JSON format, without any other information.
    
    AVAILABLE TASKS AND RESOURCES:
    
    {task_list}
    
    EXAMPLE OUTPUT in JSON FORMAT:
    
    "tasks": [
    {{'name': 'Data Collection', 'resources': [HuggingFace Dataset]}},
     {{'name': 'Data Pre-processing', 'resources': []}},
     {{'name': 'Model Training', 'resources': 'PyTorch'}},
     {{'name': 'Model Deployment', 'resources': ['Flask']}}
    ]
    
    """
