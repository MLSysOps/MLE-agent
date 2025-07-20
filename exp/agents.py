import json
import textwrap

from jinja2 import Template
from langchain_core.messages import ToolMessage, HumanMessage, SystemMessage
from langgraph.func import task
from rich.console import Console

from exp.utils import get_vllm_with_tools
from mle.function import (
    read_file, create_file, write_file, list_files,
    create_directory, preview_csv_data, preview_zip_structure, unzip_data
)
from mle.utils import clean_json_string
from mle.utils.component_memory import trace_component

ADVISER_SYSTEM_PROMPT = Template(
    textwrap.dedent(
        """
        You are a Machine learning expert tasked with advising on the best ML task/model/algorithm to use.
        
        Your abilities include:

        - Read and understand the dataset information and user's requirements; the requirements may include the task,
         the model (or method), and the evaluation metrics, etc. You should always follow the user's requirements.
        - You should briefly analyze the user's dataset and give a summary of the dataset; the dataset input can be
         a public dataset name or a path to a local CSV file.
        - And then you should always use the function `search_arxiv` or `search_papers_with_code` to search the
         newest machine learning tasks/models/algorithms that can be used to solve the user's requirements,
          and stay up to date with the latest.
        - You should provide the paper reference links of the task/model/algorithm/metric you suggest. You use the
         search results from the function `search_arxiv` or `search_papers_with_code` by generated search keywords.
        - The suggestion should be as detailed as possible, include the SOTA methods for data processing, feature
         extraction, model selection, training/sering methods and evaluation metrics. And the reasons why you suggest.
        - You should help the user to decide which framework/tools to use for the project, e.g., PyTorch, sklearn,
         MLFlow, W&B, etc. PyTorch is preferred for deep learning tasks.
        {{ "- You should also use the function `web_search` to search for articles, papers, or tutorials related to the
         task/model/algorithm/metric to help you decide which one to use.  " if config_data.get('search_key') else "" }}
         
        JSON Output Format:
        {
            "task":"xxxxx",
            "model_or_algorithm":"xxxx",
            "frameworks": ["PyTorch"],
            "reference": ["xxxx", "xxxx"],
            "evaluation_metric": ["xxx", "xxx"],
            "training_method": "xxxx",
            "device": "xxxx",
            "data_summary": "The data provided is a..., it contains...",
            "suggestion": "Based on the user requirement, we suggest you to..."
        }
        """
    )
)

ADVISOR_PROMPT = Template(textwrap.dedent(
    """
    Kaggle Challenge for {{ competition_type }} competition
    ---
    {{ description }}
    ---
    Submission file: {{ submission_file }}
    ---
    Sample submission file: {{ sample_submission }}
    """.strip()
))

PLANNER_SYSTEM_PROMPT = Template(
    textwrap.dedent(
        """
        You are a **Kaggle Solution Planner**. Produce a *concise, execution‑ready* ordered task list guiding creation of a **single `solution.py`** that trains models and writes `submission.csv` optimized for the competition’s primary metric (use its exact name; if unknown, put a placeholder like `<PRIMARY_METRIC>`).
        
        **Instructions:**
        
        * Focus only on what is necessary to reach a strong baseline and quick iterative improvements.
        * Emphasize reproducibility, robust cross‑validation aligned with data structure (e.g., stratified, time-based).
        * Include minimal but high‑impact feature engineering and model ensembling steps (e.g., Deep Model, LightGBM + optional secondary model).
        * Include saving of out-of-fold predictions (if useful) and final `submission.csv`.
        * Avoid extraneous theory—just actionable steps.
        
        # Output JSON Schema
        Each task object must have:
          - `task`: short imperative label.
          - `description`: crisp bullet-like instructions (can contain semicolons) telling the coder exactly what to implement.
        ```json
        {
          "tasks": [
            { "task": "Setup", "description": "..." },
            { "task": "Load Data", "description": "..." }
          ]
        }
        ```
        
        # Example (Illustrative Only)
        ```json
        {
          "tasks": [
            {
              "sub_task": "Setup",
              "description": "Import libs (pandas,numpy,lightgbm,sklearn); define SEED=42; set numpy/pytorch/random seeds; parse optional args for data paths and model params."
            },
            {
              "sub_task": "Data Preprocessing",
              "description": "Read train.csv with dtype optimizations (downcast numerics, category for high-card cols); perform basic cleaning and feature engineering; split into five folds"
            },
            {
              "sub_task": "Model Definition",
              "description": "Define LightGBM model with initial params (num_leaves, n_estimators); optionally define CatBoost/XGBoost models."
            },
            {
              "sub_task": "Model Training",
              "description": "For each fold: fit LightGBM with tuned params (learning_rate, num_leaves, n_estimators, early_stopping_rounds) on train fold; eval on valid fold using `<PRIMARY_METRIC>`; save best iteration; collect OOF preds."
            },
            {
              "sub_task": "Inference",
              "description": "Generate per-fold test predictions (model.predict); average across folds (and models if blended); create test DataLoader with same transforms; generate predictions with model.eval(); produce final prediction vector."
            },
            {
              "sub_task": "Evaluation Summary",
              "description": "Print per-fold and mean `<PRIMARY_METRIC>`; if classification also shows confusion matrix / AUC (if relevant); Save model weights and submission.csv"
            },
          ]
        }
        ```""".strip()
    )
)

PLAN_PROMPT = Template(textwrap.dedent(
    """
    Advisor Report:
    {{ advisor_report }}
    Submission File: {{ submission_file }}
    """.strip()
))

CODER_SYSTEM_PROMPT = Template(
    textwrap.dedent(
        """
        You are a **Machine Learning Engineer** tasked with implementing a solution based on the provided requirements by the advisor.
        You will be given the whole project plan, and each task will be provided to you one by one.
        Requirements: {{ problem }}
        Implementation Plan: {{ plan }}
        Working Directory: {{ working_dir }}
        
        Your task is to generate the complete, working Python code that implements the solution. Call the write_file, mkdir, and read_file function tools to inspect and generate the necessary files.
        IMPORTANT: 
        1. Generate a single file `solution.py` that contains all the code for the solution, including imports, constants, functions, classes, main guard (`if __name__ == "__main__":`), argument parsing (if needed), execution logic, and docstrings.
        Focus on:
        1. Clean, readable code
        2. Proper data handling
        3. Model implementation
        4. Training and evaluation logic
        5. Kaggle submission format
        
        After finalizing the code, you will call the `create_file` function to save the code to `solution.py`
        After the tool calling result is given back, you should also provide the dependencies required to run the code and the command to run the code in a JSON format:
        {
            "dependency": ["pkg1", "pkg2", "..."],
            "command": "python solution.py"
        }
        """.strip()
    )
)

CODE_PROMPT = Template(
    """
    ## Task: {{ task }}
    {{ description }}
    """
)


class AdviseAgent:
    def __init__(self, model: str, working_dir='.', console=None):
        """
        AdviseAgent: the agent to suggest which machine learning task/model/dataset to use based on the user's
        requirements. The return of the agent is an instruction to the user to modify the code based on the logs and
        web search.

        Args:
            model: the model to use.
            console: the console to use.
        """
        self.report = None
        self.model = get_vllm_with_tools(
            model, [
                list_files,
                preview_csv_data,
                preview_zip_structure,
            ]
        )
        self.chat_history = []
        self.console = console or Console()
        self.working_dir = working_dir

        self.chat_history.append(
            SystemMessage(
                content=ADVISER_SYSTEM_PROMPT.render(config_data=dict())
            )
        )

    @trace_component("advisor")
    def set_environment(self, env: dict):
        """
        Set the environment for the advisor agent.
        Args:
            env: the environment to set.
        """
        self.chat_history.append(
            HumanMessage(content="Current environment: " + json.dumps(env, indent=2))
        )

    @task
    @trace_component("advisor")
    def suggest(
        self,
        description: str,
        competition_type: str,
        submission_file: str,
        sample_submission_file: str,
    ):
        """
        Handle the query from the model query response.
        Args:
            requirement: the user requirement.
        """
        with self.console.status("MLE Advisor is thinking of the best strategy to help you..."):
            self.chat_history.append(HumanMessage(
                content=ADVISOR_PROMPT.render(
                    competition_type=competition_type,
                    description=description,
                    submission_file=submission_file,
                    sample_submission=sample_submission_file
                )
            ))
            message = self.model.invoke(self.chat_history)

            self.chat_history.append(message)
            try:
                suggestions = json.loads(message.content)
            except json.JSONDecodeError as e:
                suggestions = clean_json_string(message.content)

        return suggestions


class PlanAgent:

    def __init__(self, model, working_dir='.', console=None):
        """
        PlanAgent: the agent to plan the machine learning project. By receiving the user's requirements, the agent will
        first analyze the requirements and ask the user to provide more details if necessary. Then the agent will
        generate the project plan based on the requirements and the user's input.

        The project plan will be sent to the advisor agent to provide suggestions on the best machine learning task,
        model, dataset, and evaluation metrics to use.

        Args:
            model: the model to use.
        """
        self.console = console or Console()
        self.working_dir = working_dir
        self.model = model
        self.chat_history = []
        self.chat_history.append(
            SystemMessage(
                content=PLANNER_SYSTEM_PROMPT.render(config_data=dict())
            )
        )

    @trace_component("planner")
    def set_environment(self, env: dict):
        """
        Set the environment for the planner agent.
        Args:
            env: the environment to set.
        """
        self.chat_history.append(
            HumanMessage(content="Current environment: " + json.dumps(env, indent=2))
        )

    @task
    @trace_component("planner")
    def plan(
        self,
        advisor_report: dict,
        submission_file: str,
    ):
        """
        Handle the query from the model query response.
        Args:
            advisor_report: the report from the advisor agent.
            submission_file: the path to the submission file.
        """
        with self.console.status("MLE Planner is planning the coding tasks..."):
            self.chat_history.append(
                HumanMessage(
                    content=PLAN_PROMPT.render(
                        description=json.dumps(advisor_report, indent=2),
                        submission_file=submission_file,
                    )
                )
            )
            message = self.model.invoke(self.chat_history)

            self.chat_history.append(message)

        try:
            return json.loads(message.content)
        except json.JSONDecodeError as e:
            return clean_json_string(message.content)


class CodeAgent:

    def __init__(self, model_name, working_dir='.', console=None):
        """
        CodeAgent: the agent to solve the given coding problem by planning coding tasks, searching websites,
        and generating code snippets. It does not execute the code, only make use of built-in functions to provide
         the code snippets to solve the problem.

        Args:
            model_name: the model name to use.
            working_dir: the working directory.
            console: the console to use.
        """
        self.model = get_vllm_with_tools(
            model_name,
            [
                read_file,
                create_file,
                write_file,
                list_files,
                create_directory,
                preview_csv_data,
                preview_zip_structure,
                unzip_data,
            ]
        )
        self.chat_history = []
        self.working_dir = working_dir
        self.console = console or Console()

    @trace_component("coder")
    def setup(self, env, problem: dict, plan: dict):
        """
        Setup the coder agent with the environment, problem, and plan.
        Args:
            env: the environment to set.
            problem: the problem to solve.
            plan: the overall plan to follow.
        """
        self.chat_history.append(
            SystemMessage(
                content=CODER_SYSTEM_PROMPT.render(
                    working_dir=self.working_dir,
                    problem=json.dumps(problem, indent=2),
                    plan=json.dumps(plan, indent=2)
                )
            )
        )
        self.chat_history.append(
            HumanMessage(content="Current environment: " + json.dumps(env, indent=2))
        )

    @task
    @trace_component("coder")
    def code(self, task_dict: dict):
        """
        Handle the query from the model query response.
        Args:
            task_dict: the task dictionary.
        """

        with self.console.status(f"Coder is working on the task: {task_dict.get('task')}..."):
            self.chat_history.append(
                HumanMessage(CODE_PROMPT.render(
                        task=task_dict.get('task'),
                        description=task_dict.get('description')
                ))
            )
            message = self.model.invoke(self.chat_history)

            self.chat_history.append(message)
            code_summary = clean_json_string(message.content)
            code_summary.update({'task': task_dict.get('task'), 'task_description': task_dict.get('description')})
        return code_summary
