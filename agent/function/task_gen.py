import json
from agent.templates import load_yml


def plan_generator(requirement: str, llm_agent):
    prompt = f"""
    You are an assistant that helps generate machine learning project plans based on the user's requirements.
    The plan includes a list of tasks that can achieve the user's requirements.
    
    You should use the tasks defined in the task pool to generate a list,
     and generate the proper task description based on the user's requirements.
    
    Available tasks:
    
    {json.dumps(load_yml('task_pool.yml'))}
    
    An example output is:
    
    Tasks: [
        {{'name': 'Identify Data Sources', 'description': 'Identify the data sources for the project.'}},
        {{'name': 'Data Pre-processing', 'description': 'Pre-process the data for the model training.'}},
        {{'name': 'Model Training', 'description': 'Train the model using the pre-processed data.'}},
    ]
    
    Output: {{output}}
    
    """

    chat_history = [
        {"role": 'system', "content": prompt},
        {"role": 'user', "content": requirement}
    ]
    resp = llm_agent.completions(chat_history, stream=False)
    return resp.choices[0].message.content
