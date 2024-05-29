import json

from agent.hub import load_yml
from agent.utils.prompt import pmpt_task_desc, pmpt_plan


def req_based_generator(requirement: str, sys_prompt: str, llm_agent):
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
