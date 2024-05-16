import click
import questionary

import agent
from agent.utils import *
from agent.model import OpenAIModel
from agent.prompt import pmpt_sys_init
from agent.function import Chat, Chain

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
def start():
    """
    start: start the chat with LLM.
    """
    # check the system configuration
    configuration = Config()
    if configuration.read() is None:
        build_config()

    project_plan_file = os.path.join(configuration.read()['project']['path'], CONFIG_PROJECT_FILE)
    chain = Chain(load_plan(str(project_plan_file)), load_model())
    chain.start()


@cli.command()
def chat():
    """
    chat: start an interactive chat with LLM to work on your ML project.
    """
    # check the system configuration
    configuration = Config()
    if configuration.read() is None:
        build_config()

    model = load_model()
    console.log("Welcome to MLE-Agent! :sunglasses:")
    if model:
        console.log(f"Model loaded: {model.model_type}, {model.model}")
    console.line()

    if configuration.read().get('project') is None:
        console.log("You have not set up a project yet.")
        console.log("Please create a new project first using 'mle new' command.")
        return

    project_path = configuration.read()['project']['path']
    project_plan = read_project_plan(str(os.path.join(project_path, CONFIG_PROJECT_FILE)))
    console.log("> Current project:", project_path)

    selected_language = project_plan.lang
    console.log("> Project language:", selected_language)

    # start the interactive chat
    console.line()
    chat_app = Chat(model)
    # set the initial system prompt
    chat_app.add(role='system', content=pmpt_sys_init(selected_language, project_plan))
    chat_app.start()


@cli.command()
@click.argument('name')
def new(name):
    """
    new: create a new machine learning project with the given NAME.
    """
    if not name:
        console.log("Please provide a valid project name. Aborted.")
        return

    configuration = Config()

    description = questionary.text("What is the description of this project? (Optional)").ask()
    language = questionary.text("What is the major language for this project?").ask()

    if not language:
        console.log("Please provide a valid language. Aborted.")
        return

    project_path = create_directory(name)
    update_project_plan(
        project_path,
        {
            'name': name,
            'current_task': 0,
            'description': description,
            'llm': configuration.read()['general']['platform'],
            'project': project_path,
            'lang': language
        }
    )

    # write the project configuration
    configuration.write_section(
        CONFIG_SEC_PROJECT, {
            'path': project_path
        }
    )


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