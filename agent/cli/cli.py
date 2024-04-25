import click
import questionary

import agent
from agent.utils import *
from agent.model import OpenAIModel
from agent.prompt import pmpt_sys_init

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
    api_key = questionary.text("What is your OpenAI API key?").ask()

    general_config = {
        'platform': platform,
        'api_key': api_key,
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


def load_model():
    """
    load_model: load the model based on the configuration.
    """
    configuration = Config()
    config_dict = configuration.read()
    plat = config_dict['general']['platform']

    model = None
    if plat == LLM_TYPE_OPENAI:
        model = OpenAIModel(
            api_key=config_dict[CONFIG_SEC_GENERAL][CONFIG_SEC_API_KEY],
            model=config_dict[LLM_TYPE_OPENAI].get('model'),
            temperature=float(config_dict[LLM_TYPE_OPENAI]['temperature'])
        )

    return model


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
def chat():
    """
    chat: start an interactive chat with LLM to work on your ML project.
    """
    configuration = Config()
    model = load_model()
    console.log("Welcome to MLE-Agent! :sunglasses:")
    if model:
        console.log(f"Model loaded: {model.model_type}, {model.model}")
    console.line()

    if configuration.read().get('project') is None:
        console.log("You have not set up a project yet.")
        console.log("Please create a new project first using 'mle new <project_name>' command.")
        return

    # ask for the project language.
    console.log("> Current project:", configuration.read()['project']['path'])
    if configuration.read()['project'].get('lang') is None:
        lang = questionary.text("What is your major language for this project?").ask()
        configuration.write_section(CONFIG_SEC_PROJECT, {'lang': lang})

    selected_language = configuration.read()['project']['lang']
    console.log("> Project language:", selected_language)

    # start the interactive chat
    console.line()
    chat_app = Chat(model)
    # set the initial system prompt
    chat_app.add(role='system', content=pmpt_sys_init(selected_language))
    chat_app.start()


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


@cli.command()
@click.argument('path', nargs=-1, type=click.Path(exists=True))
def set_project(path):
    """
    project: set the current project.
    :return:
    """
    configuration = Config()
    project_path = " ".join(path)
    project_config_path = os.path.join(project_path, CONFIG_PROJECT_FILE)
    if not os.path.exists(project_config_path):
        console.log("The project path is not valid. Please check if `project.yml` exists and try again.")
        return

    configuration.write_section(CONFIG_SEC_PROJECT, {
        'path': project_path
    })

    console.log(f"> Project set to {project_path}")
