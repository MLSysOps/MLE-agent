import configparser
import os
import sys
from pathlib import Path

import questionary
from rich.console import Console

from agent.types.const import *

CONFIG_HOME = os.path.join(str(Path.home()), ".mle")
CONFIG_PATH = os.path.join(CONFIG_HOME, "config")


class Config:
    """
    Config: the overall system configuration for MLE-agent
    """

    def __init__(self):
        self.home = CONFIG_HOME
        Path(self.home).mkdir(parents=True, exist_ok=True)

        self.config_path = CONFIG_PATH
        self.config = configparser.ConfigParser()
        self.config.read(self.config_path)

    def read(self):
        """
        read: read the configuration file.

        Returns: a dictionary of the configuration.
        """
        if os.path.isfile(CONFIG_PATH):
            self.reload_config(CONFIG_PATH)
        else:
            return None

        config_dict = {}
        for section in self.config.sections():
            options_dict = {option: self.config.get(section, option) for option in self.config.options(section)}
            config_dict[section] = options_dict

        return config_dict

    def reload_config(self, config_path):
        """
        reload_config: The default configuration will load ~/.mle/config, if user want to specify
        customize, the method is required.

        @param config_path: the path of new configuration file.
        """
        self.config.read(config_path)

    def load_openai_config(self):
        """
        load_openai_config: load a OpenAI configuration when required.
        """
        if self.config.has_section(LLM_TYPE_OPENAI):
            return self.config[LLM_TYPE_OPENAI]
        else:
            raise ValueError("there is no '[openai]' section found in the configuration file.")

    def write_section(self, section_name: str, config_dict: dict, overwrite: bool = True):
        """
        write_section: write the project configuration.

        @param section_name: the section name.
        @param config_dict: the configuration dictionary.
        @param overwrite: a boolean indicating whether to overwrite the existing configuration.

        """
        if not self.config.has_section(section_name):
            self.config.add_section(section_name)

        # save the new configuration and reload.
        with open(self.config_path, 'w') as configfile:
            if overwrite:
                self.config[section_name] = config_dict
                self.config.write(configfile)
                self.reload_config(self.config_path)
            else:
                existing_config = dict(self.read().get(section_name))
                existing_config.update({key: value for key, value in config_dict.items() if key not in existing_config})
                self.config[section_name] = existing_config
                self.config.write(configfile)
                self.reload_config(self.config_path)


configuration = Config()
console = Console()


def build_config(general: bool = False):
    """
    build_config: build the configuration for MLE-agent.
    Args:
        general: a boolean indicating whether to build the general configuration only.
    :return:
    """
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
