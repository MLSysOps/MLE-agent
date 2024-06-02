import json
import os

import questionary
from rich.console import Console

from agent.hub import load_yml
from agent.utils import update_project_state
from agent.utils.prompt import pmpt_task_desc, pmpt_plan


def pmpt_plan_filename(lang: str) -> str:
    file_extension = {
        'Python': '.py',
        'JavaScript': '.js',
        'Java': '.java',
        # Add other languages and their extensions as needed
    }.get(lang, '.py')  # Default to .txt if the language is not listed

    return f"""
    You are a Machine Learning Engineer working on a project that primarily uses {lang}.
    Your task is to generate 5 file names based on the given user requirements.
    Ensure that the file suffix is correct for the specified language, which is '{file_extension}' for {lang}.

    Please generate 5 potential file names to allow the user to choose.

    Example output:
    ['train{file_extension}', 'data_loading{file_extension}', 'test_cases{file_extension}',
    'model_serve{file_extension}', 'utils{file_extension}']
    """


def gen_file_name(project, llm_agent):
    console = Console()
    prompt_message = pmpt_plan_filename(project.lang)

    with console.status("Preparing entry file name..."):
        chat_history = [
            {"role": 'system', "content": prompt_message},
            {"role": 'user', "content": project.requirement}
        ]
        file_name_candidates = llm_agent.query(chat_history)

        # If the output is a single string containing list representation, convert it properly
        if isinstance(file_name_candidates, str) and file_name_candidates.startswith(
                '[') and file_name_candidates.endswith(']'):
            import ast
            try:
                file_name_candidates = ast.literal_eval(file_name_candidates)
            except ValueError as e:
                console.log(f"Error parsing filenames: {e}")
                file_name_candidates = []  # Fallback to an empty list if parsing fails

        file_path_candidates = [os.path.join(project.path, filename.strip("'")) for filename in file_name_candidates]

    entry_file = questionary.select("Please select the file name:", choices=file_path_candidates).ask()
    # Update the project entry file and clear the chat history
    project.entry_file = entry_file
    chat_history = []

    update_project_state(project)

    return entry_file


def pmpt_dataset_detect():
    # Load and format the dataset names for display
    data_options = load_yml('data.yml')

    return f"""
    You are an machine learning engineer tasked with detecting the appropriate dataset based on user requirements.

    Instructions:
    - Detect the data source based on the user's specific requirements.
    - If the requirement does not specify a data source, use the default response: 'no_data_information_provided'.

    Available Data Sources:
    {data_options}

    Output:
    - Provide only the name of the dataset from the list, without any punctuation or additional formatting.
    """


def analyze_requirement(requirement: str, sys_prompt: str, llm_agent):
    """
    Generate the project plan based on the user's requirements.
    :param requirement: the user's requirements.
    :param sys_prompt: the system prompt.
    :param llm_agent: the language model agent.
    :return: the project plan.
    """
    chat_history = [
        {"role": 'system', "content": sys_prompt},
        {"role": 'user', "content": requirement}
    ]
    return llm_agent.query(chat_history)


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
    return json.loads(llm_agent.query(chat_history))


def plan_generator(
        requirement: str,
        llm_agent,
):
    """
    Generate the project plan based on the user's requirements.
    :param requirement: the user's requirements.
    :param llm_agent: the language model agent.
    :return: the project plan.
    """
    task_list = []
    for task in load_yml('plan.yml'):
        task_list.append(
            {
                'name': task['name'],
                'prompt': task['prompt'],
                'resources': [r['name'] for r in task.get('resources')]
            }
        )
    chat_history = [
        {"role": 'system', "content": pmpt_plan(json.dumps(task_list))},
        {"role": 'user', "content": requirement}
    ]
    target_tasks = llm_agent.query(chat_history)

    # generate the completed plan with detailed description
    return description_generator(requirement, target_tasks, llm_agent)
