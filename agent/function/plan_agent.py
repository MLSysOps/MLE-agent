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


def pmpt_task_select():
    task_list = load_yml('task.yml')

    return f"""
    As an ML project expert, you are tasked with selecting the most appropriate tasks based on the user's requirements
    and provided data samples.

    Instructions:
    - Analyze the provided user requirements and data samples carefully.
    - Select three tasks that are most relevant to the requirements.
    - For each selected task, provide a one-sentence description explaining its relevance.

    Available Tasks:
    {task_list}

    Output Format:
    Your response should include three entries formatted as a list of strings, where each string contains the task name followed by its description, e.g.:
    ["Task1, Description of Task1", "Task2, Description of Task2", "Task3, Description of Task3"]

    Note: Return only the task names followed by a brief description, without any additional information or punctuation.
    """


def pmpt_model_select():
    return f"""
    As an ML project expert, you are tasked with recommending three different AI model architectures based on the
    user's requirements, provided data samples, and selected ML tasks. Each recommended model should align with one
    of the specific criteria: best overall performance, balanced performance, and fastest computation.

    Instructions:
    - Analyze the provided user requirements, data samples, and ML tasks.
    - Select three models:
        1. The best performing model in terms of accuracy.
        2. A model with balanced performance considering both accuracy and computational efficiency.
        3. The fastest model in terms of computational speed.
    - For each model, provide a brief one-sentence summary that includes its suitability for the targeted task, its
    accuracy, and its speed.

    Output Format:
    Please return a list of three strings, where each string includes the model's name followed by its summary.
    Ensure the description highlights how the model meets one of the selection criteria (best, balanced, fastest).
    Example format:
    ["ModelName1, Best for task X with high accuracy of Y%, suitable for complex data analysis.",
     "ModelName2, Balanced model, offers moderate accuracy with better speed, good for real-time applications.",
     "ModelName3, Fastest model with lower accuracy, best for quick processing where speed is prioritized over precision."]

    Note: Ensure that the architecture names with summary are returned without any additional punctuation.
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
