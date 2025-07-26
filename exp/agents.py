import json
import re
import textwrap
from typing import TypedDict, cast

from jinja2 import Template
from langchain_core.messages import ToolMessage, HumanMessage, SystemMessage, BaseMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from rich.console import Console

from exp.decorators import method_task, method_entrypoint
from exp.utils import get_vllm_with_tools, safe_fileio
from mle.function import (
    read_file, create_file, list_files,
    create_directory, preview_csv_data, preview_zip_structure, unzip_data, execute_command
)
from mle.utils import clean_json_string

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
        ---
        Current Environment:
        {{ env | tojson(indent=2) }}
        
        ---
        ### Output JSON Schema
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
        
        `### Example (Illustrative Only)
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
        Advise the coding tasks based on the following requirements:
        {{ advisor_report | tojson(indent=2) }}
        ---
        Refer to the dataset structure preview on the submission file and example submission file, below are their paths:
        Submission file: {{ submission_file }}
        Sample submission file: {{ sample_submission_file }}
        """.strip()
    )
)

CODER_SYSTEM_PROMPT = Template(
    textwrap.dedent(
        """
        You are a **Machine Learning Engineer** executing SMALL, ORDERED tasks.
        
        ### Context
        - advisor_report: {{ advisor_report | tojson(indent=2) }}
        - working_dir: {{ working_dir }}
        - env: {{ env | tojson(indent=2) }}
        
        ### GOLDEN RULE
        **Implement ONLY what the "Current Task" asks for.**
        Do NOT add future pipeline pieces unless the task explicitly says to finalize the whole solution.
        
        ### FILE CONTRACT
        - All code must live in ONE file: `solution.py`.
        - Every time you modify code, you must output the **entire final content** of `solution.py` (no diffs/patches).
        - Always end your response with exactly ONE `create_file` tool call to write/overwrite `solution.py`. Nothing after that call.
        
        ### TOOL USAGE
        - Use any inspection tools before guessing (e.g., to view data/file tree).
        - But the final step is always the `create_file` call.
        
        ### OUTPUT PROCEDURE
        1. **THINK**: Briefly state what you will do (≤3 bullet points).
        2. **INSPECT**: If needed, use tools to inspect data/files.
        3. **CODE**: Write the code for the task in `solution.py`.
        4. **TOOL CALL**: Always end with a `create_file` tool call to write the code.
        
        ### SAFETY RAILS
        - If the task is too broad or conflicts with the Golden Rule, state the issue and request clarification.
        - ≤ 100 LOC per task unless the task says to “FINALIZE”, “FULL SOLUTION” etc.
        """.strip()
    )
)

CODE_PROMPT = Template(
    textwrap.dedent(
        """
        Current Task:
        {{ task }}
        {{ description }}
        
        (Remember: Only do what's here.)
        """.strip()
    )
)

CODER_DEPS_PROMPT = Template(
    textwrap.dedent(
        """
        Look at the latest created code in the chat history and analyze the dependencies required to run the code.
        Providing the dependencies required and the command to run the code in a JSON format.
        Example (for JSON schema illustration only):
        {
            "dependency": ["pkg1", "pkg2", "..."],
            "command": "python solution.py",
            "entryfile": "solution.py"
        }
        """.strip()
    )
)


class AdviseAgent:
    checkpointer = MemorySaver()

    class State(TypedDict):
        chat_history: list[BaseMessage]  # kept for backward-compat, not required anymore
        env: dict
        competition_type: str
        description: str
        submission_file: str
        sample_submission_file: str

    def __init__(self, model_name: str, console: Console | None = None):
        """
        AdviseAgent: suggests which ML task/model/dataset to use based on user's requirements.
        Returns structured suggestions/instructions to the user.
        """
        tools = [
            list_files,
            preview_csv_data,
            preview_zip_structure,
        ]
        self.model = get_vllm_with_tools(model_name, tools)
        self.console = console or Console()
        self.chat_history: list[BaseMessage] = []

    @method_task
    def setup(self, env: dict):
        """
        Initialize the conversation with the system prompt, once.
        """
        if not self.chat_history:
            self.chat_history.append(
                SystemMessage(
                    content=ADVISER_SYSTEM_PROMPT.render(config_data=dict(), env=env)
                )
            )

    @method_task
    def suggest(
        self,
        competition_type: str,
        description: str,
        submission_file: str,
        sample_submission_file: str,
    ) -> dict:
        """
        Ask the advisor model for suggestions based on the provided context.
        """
        with self.console.status("MLE Advisor is thinking of the best strategy to help you..."):
            self.chat_history.append(
                HumanMessage(
                    content=ADVISOR_PROMPT.render(
                        competition_type=competition_type,
                        description=description,
                        submission_file=submission_file,
                        sample_submission=sample_submission_file,
                    )
                )
            )
            message = self.model.invoke(self.chat_history)
            self.chat_history.append(message)

        try:
            return json.loads(message.content)
        except json.JSONDecodeError:
            return clean_json_string(message.content)

    @method_entrypoint(checkpointer=checkpointer)
    def graph(self, state: State) -> dict:
        """
        Orchestrate setup + suggestion and return advisor output.
        """
        self.setup(state["env"])
        return self.suggest(
            competition_type=state["competition_type"],
            description=state["description"],
            submission_file=state["submission_file"],
            sample_submission_file=state["sample_submission_file"],
        ).result()


class PlanAgent:
    checkpointer = MemorySaver()

    class State(TypedDict):
        advisor_report: dict
        submission_file: str
        sample_submission_file: str
        env: dict

    def __init__(self, model_name: str, working_dir: str = ".", console: Console | None = None):
        """
        PlanAgent: plans the ML project based on requirements and the advisor's report.
        """
        self.model = get_vllm_with_tools(model_name, [])
        self.working_dir = working_dir
        self.console = console or Console()
        self.chat_history: list[BaseMessage] = []

    @method_task
    def setup(self, env: dict):
        """
        Initialize the conversation with the planner system prompt, once.
        """
        if not self.chat_history:
            self.chat_history.append(
                SystemMessage(
                    content=PLANNER_SYSTEM_PROMPT.render(config_data=dict(), env=env)
                )
            )

    @method_task
    def plan(
        self,
        advisor_report: dict,
        submission_file: str,
        sample_submission_file: str,
    ) -> dict:
        """
        Ask the planner model to generate the project plan.
        """
        with self.console.status("MLE Planner is planning the coding tasks..."):
            self.chat_history.append(
                HumanMessage(
                    content=PLAN_PROMPT.render(
                        advisor_report=advisor_report,
                        submission_file=submission_file,
                        sample_submission_file=sample_submission_file,
                    )
                )
            )
            message = self.model.invoke(self.chat_history)
            self.chat_history.append(message)

        try:
            return json.loads(message.content)
        except json.JSONDecodeError:
            return clean_json_string(message.content)

    @method_entrypoint(checkpointer=checkpointer)
    def graph(self, state: State) -> dict:
        """
        Orchestrate setup + planning and return the plan.
        """
        self.setup(state["env"])
        return self.plan(
            advisor_report=state["advisor_report"],
            submission_file=state["submission_file"],
            sample_submission_file=state["sample_submission_file"],
        ).result()


class CodeAgent:
    checkpointer = MemorySaver()

    class State(TypedDict):
        advisor_report: dict
        task: str
        description: str
        env: dict

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
        tools = [
            safe_fileio(working_dir)(read_file),
            safe_fileio(working_dir, path_params=["path"])(create_file),
            safe_fileio(working_dir)(list_files),
            safe_fileio(working_dir, path_params=["path"])(create_directory),
            safe_fileio(working_dir, path_params=["path"])(preview_csv_data),
            safe_fileio(working_dir, path_params=["path"])(preview_zip_structure),
            safe_fileio(working_dir, path_params=["extract_path"])(unzip_data),
        ]

        self.model = get_vllm_with_tools(model_name, tools)
        self.working_dir = working_dir
        self.console = console or Console()
        self.tool_node = ToolNode(tools)
        self.chat_history: list[BaseMessage] = []

    @method_task
    def setup(self, advisor_report: dict, env: dict):
        # Set up the chat history with the system prompt if not already set
        if len(self.chat_history) == 0:
            self.chat_history.append(
                SystemMessage(
                    content=CODER_SYSTEM_PROMPT.render(
                        working_dir=self.working_dir,
                        advisor_report=advisor_report,
                        env=env,
                    )
                )
            )

    @method_task
    def code(self, task: str, description: str, first_call=True) -> AIMessage:
        """
        Handle the query from the model query response.
        Args:
            task: the task to solve.
            description: the description of the task.
            first_call: whether this is the first call to the code task.
        """

        with self.console.status(f"Coder is working on the task: {task}..."):
            if first_call:
                self.chat_history.append(
                    HumanMessage(
                        CODE_PROMPT.render(
                            task=task,
                            description=description,
                        )
                    )
                )
            message = cast(AIMessage, self.model.invoke(self.chat_history))

            self.chat_history.append(message)
            return message

    @method_task
    def deps(self) -> dict:
        """
        Get the dependencies required to run the code and the command to run the code.
        Returns:
            A dictionary containing the dependencies and the command to run the code.
        """
        self.chat_history.append(
            HumanMessage(content=CODER_DEPS_PROMPT.render())
        )
        message = self.model.invoke(self.chat_history)

        self.chat_history.append(message)
        try:
            return json.loads(message.content)
        except json.JSONDecodeError as e:
            return clean_json_string(message.content)

    @method_task
    def verify_code(self, python_exec: str, dependency: list[str], command: str) -> dict:
        """
        Installs missing dependencies and runs the provided command using the venv.
        """
        working_dir = self.working_dir
        results = {}

        # Step 1: Detect missing dependencies
        missing_deps = []
        for dep in dependency:
            check_cmd = f'{python_exec} -c "import {dep}"'
            check_result: dict = execute_command(check_cmd, raw=True)
            self.console.log(f"Checking dependency: [yellow]{dep}[/yellow]")
            if check_result['exit_code'] != 0:
                missing_deps.append(dep)

        self.console.print(f"Found missing dependencies: {missing_deps}", style="bold yellow")

        # Step 2: Batch install if needed
        if missing_deps:
            install_cmd = f"{python_exec} -m pip install {' '.join(missing_deps)}"
            install_result = execute_command(install_cmd, cwd=working_dir, raw=True)
            self.console.log(f"Executing command: [yellow]{install_cmd}[/yellow]")
            results["install"] = {
                "dependencies": missing_deps,
                "exit_code": install_result["exit_code"],
                "stdout": install_result["stdout"],
                "stderr": install_result["stderr"],
            }
        else:
            results["install"] = "all dependencies already installed"
        self.console.print(f"Installed: {results['install']}", style="bold green")

        # Step 3: Run the main command
        # Replace 'python' / 'python3' command world with the provided python_exec, use regex to ensure it works
        command = re.sub(r'\bpython[3]?\b', python_exec, command)
        run_result = execute_command(command, cwd=working_dir, raw=True)
        self.console.log(f"Executing command: [yellow]{command}[/yellow]")
        results["execution"] = {
            "exit_code": run_result["exit_code"],
            "stdout": run_result["stdout"],
            "stderr": run_result["stderr"],
        }
        self.console.log(f"Executed command: {command}, return {run_result['exit_code']}", style="bold green")

        return results

    @method_entrypoint(checkpointer=checkpointer)
    def graph(self, state: State) -> dict:
        """
        Call the agent to get the code for the task.
        Args:
            state: the state of the agent containing the task and description.
        Returns:
            The code for the task.
        """
        self.setup(state['advisor_report'], state['env'])

        try_times = 5
        while try_times > 0:
            message = self.code(
                task=state['task'],
                description=state['description'],
                # first_call=(try_times == 5)
            ).result()
            try_times -= 1
            if message.tool_calls:
                self.console.print(f"Calling tools {[tool['name'] for tool in message.tool_calls]}")
                message = self.tool_node.invoke(
                    {
                        "messages": [message],
                    }
                )
                self.chat_history.extend(message['messages'])

                # If the tool `create_file` succeeded, break the loop
                if any(
                    isinstance(msg, ToolMessage) and msg.name == "create_file" and
                    msg.content and "error" not in msg.content.lower()
                    for msg in message['messages']
                ):
                    break
            else:
                break

        # Check the dependencies and command to run the code
        deps = self.deps().result()

        # Execute the code and check if successful
        if deps.get("dependency") and deps.get("command"):
            results = self.verify_code(
                python_exec=deps.get("python_exec", "python3"),
                dependency=deps["dependency"],
                command=deps["command"]
            ).result()
            deps["results"] = results
        else:
            self.console.print("No dependencies or command found, skipping execution.", style="bold red")

        return deps
