import click
import inquirer

import agent
from agent.utils import *

console = Console()
# avoid the tokenizers parallelism issue
os.environ['TOKENIZERS_PARALLELISM'] = 'false'


def build_config(general: bool = False):
    """
    build_config: build the configuration for Termax.
    Args:
        general: a boolean indicating whether to build the general configuration only.
    :return:
    """
    configuration = Config()
    platform = LLM_TYPE_OPENAI
    exe_questions = [
        inquirer.Text(
            "api_key",
            message="What is your OpenAI API key?"
        )
    ]

    general_config = {
        'platform': platform,
        'api_key': inquirer.prompt(exe_questions)['api_key'],
    }

    configuration.write_section(CONFIG_SEC_GENERAL, general_config)

    if not general:
        platform_config = {
            "model": 'gpt-3.5-turbo',
            'temperature': 0.7,
            'max_tokens': 2000,
            'top_p': 1.0,
            'top_k': 32,
            'stop_sequences': 'None',
            'candidate_count': 1
        }

        configuration.write_section(platform, platform_config)


@click.group()
@click.version_option(version=agent.__version__)
def cli():
    """
    MLE-Agent: The CLI tool to build machine learning projects.
    """
    pass


@cli.command()
@click.option('--general', '-g', is_flag=True, help="Set up the general configuration for MLE Agent.")
def config(general):
    """
    Set up the global configuration for Termax.
    """
    build_config(general)


@cli.command()
@click.argument('text', nargs=-1)
def ask(text):
    """
    ASK the agent a question to build an ML project.
    """

    console.log(text)


@cli.command()
@click.argument('name')
def new(name: str):
    """
    new: create a new machine learning project.
    """
    configuration = Config()
    project_initial_config = {
        'name': name,
        'description': 'A new machine learning project.',  # default description
        'llm': configuration.read()['general']['platform'],
        'step': 0
    }

    project_path = create_directory(name)
    update_project_state(project_path, project_initial_config)
    configuration.write_section(CONFIG_SEC_PROJECT, {
        'path': project_path
    })
