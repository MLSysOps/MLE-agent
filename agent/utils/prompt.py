from agent.hub import load_yml
from agent.types import Project
from .system import read_file_to_string


def pmpt_chat_init(project: Project) -> str:
    current_task = project.plan.tasks[project.plan.current_task - 1]
    target_source_code = read_file_to_string(project.entry_file)
    if target_source_code is None:
        return f"""
        You are an Machine learning engineer, and you are currently working on an ML project using {project.lang}
         as the primary language. And now you should answer the user's questions based on the following information.
        
        USEFUL INFORMATION:
        
        - Project Language: {project.lang}
        - Your project plan: {project.plan.dict()}
        - The current task you are working on: {current_task.dict()}
        
        """
    else:
        return f"""
        You are an Machine learning engineer, and you are currently working on an ML project using {project.lang}
         as the primary language. And now you should answer the user's questions based on the following information.
        
        USEFUL INFORMATION:
        
        - Project Language: {project.lang}
        - Your project plan: {project.plan.dict()}
        - The current task you are working on: {current_task.dict()}
        - The source code you have written for the whole project: {read_file_to_string(project.entry_file)}
        
        """


def pmpt_public_dataset_guess():
    return f"""
    As an ML project expert, you provide consultation to users based on their specific requirements for datasets.

    Task:
    - Select three datasets that best meet the user's project requirements.
    - For each dataset, provide a one-sentence summary that explains why the dataset is appropriate for the project.

    Instructions:
    - Return the names of the datasets, each followed by a brief summary, formatted as entries in a list.
    - Each entry in the list should be a string containing the dataset name followed directly by a comma and the summary.

    Output Format:
    Your response should be formatted as a list of strings. Each string should follow this format:
    "Dataset_Name, Summary of why the dataset is suitable.",

    Example Output:
    [
        "TrafficVolumeDataset, Contains hourly traffic volume for various highways, ideal for predictive traffic
        modeling.",
        "RetailSalesForecasting, Provides daily sales data across several retail chains, suitable for demand
        forecasting.",
        "SentimentAnalysisTweets, Comprised of labeled tweets for sentiment analysis, perfect for training NLP models.",
    ]

    Ensure your response strictly adheres to this format for clarity and consistency.
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
    You are an machine learning engineer with strong expertise in MLOps and project planning.
    You will help me generate a project plan based on the user's requirements and provided information.
    
    - Understand the user's requirements and select the appropriate tasks.
    - Use the tasks only from the following task list.
    - Understand the task requirements and select the necessary resources.
    - Use appropriate resources for each task to track the experiment and make the project reproducible.
    - Select the minimum resources necessary to achieve the requirements.
    - Return the plan in JSON format, without any other information.

    AVAILABLE TASKS AND RESOURCES:
    {task_list}

    EXAMPLE OUTPUT in JSON FORMAT:

    {{
        "tasks": [
            {{"name": "Public Datasets Collection", "resources": ["HuggingFace Datasets"]}},
            {{"name": "Data Loading", "resources": ["pandas"]}},
            {{"name": "Data Pre-processing", "resources": ["scikit-learn preprocessing"]}},
            {{"name": "Model Training", "resources": ["huggingface transformers", "wandb"]}},
            {{"name": "Model Evaluation", "resources": ["torchmetrics"]}},
        ]
    }}
    """
