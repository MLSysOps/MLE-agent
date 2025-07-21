import json
import textwrap
from typing import TypedDict, Annotated

from jinja2 import Template
from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import ToolMessage, HumanMessage, SystemMessage, BaseMessage, AIMessage
from langchain_core.runnables import Runnable
from langgraph.checkpoint.memory import MemorySaver
from langgraph.func import task, entrypoint
from langgraph.prebuilt import ToolNode
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
         
        You are working with the following environment: 
        {{ env | tojson(indent=2) }}
         
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

ADVISOR_PROMPT = Template(
    textwrap.dedent(
        """
        Kaggle Challenge for {{ competition_type }} competition
        ---
        {{ description }}
        ---
        Submission file: {{ submission_file }}
        ---
        Sample submission file: {{ sample_submission }}
        """.strip()
    )
)

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

PLAN_PROMPT = Template(
    textwrap.dedent(
        """
        Advisor Report:
        {{ advisor_report }}
        Submission File: {{ submission_file }}
        """.strip()
    )
)

CODER_SYSTEM_PROMPT = Template(
    textwrap.dedent(
        """
        You are a **Machine Learning Engineer** tasked with implementing a solution based on the provided requirements by the advisor.
        You will be given the whole project plan, and each task will be provided to you one by one.
        Requirements: {{ advisor_report | tojson(indent=2) }}
        Implementation Plan: {{ plan | tojson(indent=2) }}
        Working Directory: {{ working_dir }}
        Environment: {{ env | tojson(indent=2) }}
        
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
    console: Console = None
    model: "Runnable[LanguageModelInput, BaseMessage]"
    checkpointer = MemorySaver()

    class State(TypedDict):
        chat_history: list[BaseMessage]
        env: dict
        competition_type: str
        description: str
        submission_file: str
        sample_submission_file: str

    def __new__(cls, model_name: str, console=None):
        """
        AdviseAgent: the agent to suggest which machine learning task/model/dataset to use based on the user's
        requirements. The return of the agent is an instruction to the user to modify the code based on the logs and
        web search.

        Args:
            model_name: the model to use.
            console: the console to use.
        """
        cls.model = get_vllm_with_tools(
            model_name, [
                list_files,
                preview_csv_data,
                preview_zip_structure,
            ]
        )
        cls.console = console or Console()
        return super().__new__(cls)

    @staticmethod
    @task
    def suggest(state: Annotated[State, "State of the agent"]) -> dict:
        """
        Handle the query from the model query response.
        Args:
            chat_history: the chat history of the agent.
            description: the description of the competition.
            competition_type: the type of the competition.
            submission_file: the path to the submission file.
            sample_submission_file: the path to the sample submission file.
        """
        with AdviseAgent.console.status("MLE Advisor is thinking of the best strategy to help you..."):
            state['chat_history'].append(
                HumanMessage(
                    content=ADVISOR_PROMPT.render(
                        competition_type=state['competition_type'],
                        description=state['description'],
                        submission_file=state['submission_file'],
                        sample_submission=state['sample_submission_file']
                    )
                )
            )
            message = AdviseAgent.model.invoke(state['chat_history'])

            state['chat_history'].append(message)
            try:
                suggestions = json.loads(message.content)
            except json.JSONDecodeError as e:
                suggestions = clean_json_string(message.content)

        return suggestions

    @staticmethod
    @entrypoint(checkpointer=checkpointer)
    def graph(state: Annotated[State, "State of the agent"]) -> dict:
        """
        Call the agent to get the suggestions.
        Returns:
            The suggestions from the agent.
        """
        state['chat_history'] = [
            SystemMessage(
                content=ADVISER_SYSTEM_PROMPT.render(config_data=dict(), env=state['env'])
            )
        ]
        return AdviseAgent.suggest(state).result()


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
    model: "Runnable[LanguageModelInput, BaseMessage]"
    console: Console = None
    working_dir: str = '.'
    chat_history: list[BaseMessage] = []
    checkpointer = MemorySaver()
    tool_node: ToolNode

    class State(TypedDict):
        advisor_report: dict
        plan: dict
        task: str
        description: str
        env: dict

    def __new__(cls, model_name, working_dir='.', console=None):
        """
        CodeAgent: the agent to solve the given coding problem by planning coding tasks, searching websites,
        and generating code snippets. It does not execute the code, only make use of built-in functions to provide
         the code snippets to solve the problem.

        Args:
            model_name: the model name to use.
            working_dir: the working directory.
            console: the console to use.
        """
        tools =             [
                read_file,
                create_file,
                write_file,
                list_files,
                create_directory,
                preview_csv_data,
                preview_zip_structure,
                unzip_data,
            ]

        cls.model = get_vllm_with_tools(model_name, tools)
        cls.working_dir = working_dir
        cls.console = console or Console()
        cls.tool_node = ToolNode(tools)
        return super().__new__(cls)

    @staticmethod
    @task
    def code(task: str, description: str, first_call=True) -> AIMessage:
        """
        Handle the query from the model query response.
        Args:
            task: the task to solve.
            description: the description of the task.
            first_call: whether this is the first call to the code task.
        """

        with CodeAgent.console.status(f"Coder is working on the task: {task}..."):
            if first_call:
                CodeAgent.chat_history.append(
                    HumanMessage(
                        CODE_PROMPT.render(
                            task=task,
                            description=description,
                        )
                    )
                )
            message = CodeAgent.model.invoke(CodeAgent.chat_history)

            CodeAgent.chat_history.append(message)
        return message

    @staticmethod
    @entrypoint(checkpointer=checkpointer)
    def graph(state: State) -> dict:
        """
        Call the agent to get the code for the task.
        Args:
            state: the state of the agent containing the task and description.
        Returns:
            The code for the task.
        """
        # Set up the chat history with the system prompt if not already set
        if len(CodeAgent.chat_history) == 0:
            CodeAgent.chat_history.append(
                SystemMessage(
                    content=CODER_SYSTEM_PROMPT.render(
                        working_dir=CodeAgent.working_dir,
                        advisor_report=state['advisor_report'],
                        plan=state['plan'],
                        env=state['env'],
                    )
                )
            )

        try_times = 5
        while try_times > 0:
            message = CodeAgent.code(
                task=state['task'],
                description=state['description'],
                first_call=(try_times == 5)
            ).result()
            try_times -= 1

            if isinstance(message, AIMessage):
                # If the message is an AIMessage, check if it need tool calls
                if message.tool_calls:
                    message = CodeAgent.tool_node.invoke({
                        "messages": CodeAgent.chat_history[-1:],
                    })
                    CodeAgent.chat_history.extend(message['messages'])
                else:
                    # If no tool calls, return the message
                    CodeAgent.chat_history.append(message)
                    break
            else:
                break

        CodeAgent.console.print(CodeAgent.chat_history)
        return message
