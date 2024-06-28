import sys

import questionary
from rich.console import Console

from agent.types import Project
from agent.types.const import (
    LLM_TYPE_OPENAI,
    LLM_TYPE_OLLAMA,
    SEARCH_ENGINE_GOOGLE,
    SEARCH_ENGINE_SEARCHAPI,
    SEARCH_ENGINE_BING,
    CONFIG_SEC_GENERAL,
    CODE_LANGUAGE
)
from agent.utils import Config, read_project_state

configuration = Config()
console = Console()


def build_config(general: bool = False):
    """
    build_config: build the configuration for MLE-agent.
    Args:
        general: a boolean indicating whether to build the general configuration only.
    :return:
    """
    global platform_config
    platform = questionary.select(
        "Which language model platform do you want to use?",
        choices=[LLM_TYPE_OPENAI, LLM_TYPE_OLLAMA]
    ).ask()

    # write the Ollama configuration
    if platform == LLM_TYPE_OLLAMA:
        model = questionary.text("What is the Ollama model version?").ask()

        if not model:
            sys.exit(0)

        platform_config = {
            "model": 'llama3'
        }

    # write the OpenAI configuration
    elif platform == LLM_TYPE_OPENAI:
        api_key = questionary.text("What is your OpenAI API key?").ask()

        if not api_key:
            sys.exit(0)

        platform_config = {
            "api_key": api_key,
            "model": 'gpt-3.5-turbo',
            'temperature': 0.7,
            'max_tokens': 16_385,
            'top_p': 1.0,
            'top_k': 32,
            'stop_sequences': 'None',
            'candidate_count': 1
        }
    else:
        console.log("The platform is not supported. Aborted.")
        sys.exit(0)

    search_engine = questionary.select(
        "Which search engine do you want to use?",
        choices=[SEARCH_ENGINE_GOOGLE, SEARCH_ENGINE_SEARCHAPI, SEARCH_ENGINE_BING, "no_web_search"]
    ).ask()

    if search_engine == "no_web_search":
        search_engine_config = {}
        console.log("No web search engine is set.")
    elif search_engine == SEARCH_ENGINE_GOOGLE:
        search_key = questionary.text("What is your Google search engine key?").ask()
        search_engine_id = questionary.text("What is your Google search engine ID?").ask()
        if not search_key or not search_engine_id:
            sys.exit(0)

        search_engine_config = {
            "key": search_key,
            "endpoint": "https://customsearch.googleapis.com/customsearch/v1",
            "cx": search_engine_id,
            "refer_count": 8,
            "timeout": 5
        }
    else:
        console.log(f"The {search_engine} search is not supported. Aborted.")
        sys.exit(0)

    experiment_tracking_tool = questionary.select(
        "Which experiment tracking tool do you want to use?",
        choices=["no_exp_tracking_tool", "wandb", "mlflow"]
    ).ask()

    if experiment_tracking_tool == "no_exp_tracking_tool":
        experiment_tracking_config = {}
        console.log("No experiment tracking tool is set.")
    elif experiment_tracking_tool == "wandb":
        wandb_api_key = questionary.text("What is your Weights & Biases API key?").ask()
        if not wandb_api_key:
            sys.exit(0)
        experiment_tracking_config = {
            "tool": "wandb",
            "api_key": wandb_api_key
        }
    elif experiment_tracking_tool == "mlflow":
        mlflow_tracking_uri = questionary.text("What is your MLflow tracking URI?").ask()
        if not mlflow_tracking_uri:
            sys.exit(0)
        experiment_tracking_config = {
            "tool": "mlflow",
            "tracking_uri": mlflow_tracking_uri
        }
    else:
        console.log(f"The {experiment_tracking_tool} tracking tool is not supported. Aborted.")
        sys.exit(0)

    code_language = CODE_LANGUAGE

    need_code_rag = questionary.confirm(
        "Do you need retrieve the open-source codes from GitHub?",
    ).ask()
    github_token = None
    if need_code_rag:
        github_token = questionary.text(
            "What is your GitHub tokens for code retrival?",
        ).ask()

    general_config = {
        'platform': platform,
        'code_language': code_language,
        'search_engine': search_engine,
        'github_token': github_token,
        'experiment_tracking_tool': experiment_tracking_tool
    }

    configuration.write_section(CONFIG_SEC_GENERAL, general_config)
    if not general:
        configuration.write_section(platform, platform_config)
        configuration.write_section(search_engine, search_engine_config)
        configuration.write_section("experiment_tracking", experiment_tracking_config)


def get_project_config(reset: bool):
    if configuration.read() is None:
        console.log("Configuration file does not exist. Creating a new one...")
        build_config()

    if configuration.read().get('project') is None:
        console.log("You have not set up a project yet.")
        console.log("Please create a new project first using 'mle (kaggle) new your_project_name' command,"
                    " or set the project using 'mle set_project <project path>'.")
        return

    p = read_project_state(configuration.read()['project']['name'])
    if p is None:
        console.log("Could not find the project in the database. Aborted.")
        return

    if reset:
        console.log("Resetting the project state.")
        p = Project(
            name=p.name,
            description=p.description,
            lang=p.lang,
            llm=p.llm,
            path=p.path,
            kaggle_config=p.kaggle_config,
            kaggle_competition=p.kaggle_competition
        )

    return p
