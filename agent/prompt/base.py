from agent.types import Plan
from agent.hub import load_yml


def pmpt_sys_init(
        lang: str,
        plan: Plan
) -> str:
    return f"""
    You are an Machine learning engineer, and you are currently working on an ML project using {lang}
     as the primary language. The ML project contains multiple steps, and each step is a task that
      you need to complete by generating a code script and the corresponding file name based on the user requirements.
    
    Now, you are currently working on {plan.current_task}:{plan.tasks[plan.current_task].name} task.
    The output format should be:
    
    File Name: {{name}}
    
    Code: {{code}}
    
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


def pmpt_dataset_selection():
    return f"""
    You are an ML project expert provides consultation to the user based on the user's requirements.

    - You should choose a dataset that can achieve the user's requirements.
    - You only return the dataset name.
    - Noted: it is the name of the dataset, not the platform hosts the dataset.

    OUTPUT should only a name without any punctuation.

    """


def pmpt_dataset_detector():
    return f"""
    You are an ML project expert that detects the dataset based on the user's requirements.

    - You should detect the data source based on the user's requirements.
    - You only return the dataset name.
    - Noted: If the requirement doesn't contain the data source information, select 'no_data_information_provided'
    
    AVAILABLE OPTIONS:
    
    {load_yml('data.yml')}

    OUTPUT should only a name without any punctuation.

    """


def pmpt_model_selection():
    return f"""
    You are an ML project expert provides consultation to the user based on the user's requirements.

    - You should choose an AI model framework that can achieve the user's requirements.
    - You should only return the framework name.
    - Note: it if the model architecture name, not the framework builds the model.

    OUTPUT should only a name without any punctuation.

    """


def pmpt_task_selection():
    return f"""
    You are an ML project expert that determines the tasks based on the user's requirements.
    
    - You should select a task from the following task list.
    - You should not return other information except the task name.
    
    AVAILABLE TASKS:
    
    {load_yml('task.yml')}
    
    OUTPUT should only a name without any punctuation.
    
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
