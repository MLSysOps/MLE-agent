import sys

import click
import questionary

import agent
from agent.server import start_server
from agent.function import Chat, PlanAgent
from agent.model import OpenAIModel, OllamaModel
from agent.utils import *
from agent.utils.prompt import pmpt_chat_init

console = Console()
# avoid the tokenizers parallelism issue
os.environ['TOKENIZERS_PARALLELISM'] = 'false'


def build_config(general: bool = False):
    """
    build_config: build the configuration for MLE-agent.
    Args:
        general: a boolean indicating whether to build the general configuration only.
    :return:
    """
    configuration = Config()
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

    code_language = CODE_LANGUAGE
    general_config = {
        'platform': platform,
        'code_language': code_language
    }

    configuration.write_section(CONFIG_SEC_GENERAL, general_config)
    if not general:
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
            api_key=config_dict[LLM_TYPE_OPENAI][CONFIG_SEC_API_KEY],
            model=config_dict[LLM_TYPE_OPENAI].get('model'),
            temperature=float(config_dict[LLM_TYPE_OPENAI]['temperature'])
        )
    if plat == LLM_TYPE_OLLAMA:
        model = OllamaModel(model=config_dict[LLM_TYPE_OLLAMA].get('model'))

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
    Set up the global configuration for MLE-agent.
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

    if configuration.read().get('project') is None:
        console.log("You have not set up a project yet.")
        console.log("Please create a new project first using 'mle new your_project_name' command,"
                    " or set the project using 'mle set_project <project path>'.")
        return

    project_plan_file = os.path.join(configuration.read()['project']['path'], CONFIG_PROJECT_FILE)

    # check if the project plan file exists
    if not os.path.exists(project_plan_file):
        console.log(f"The {CONFIG_PROJECT_FILE} does not exist in the workspace. Aborted.")
        return

    chain = PlanAgent(load_plan(str(project_plan_file)), load_model())
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
    console.log("> [green]Current project:[/green]", project_path)

    selected_language = project_plan.lang
    console.log("> [green]Project language:[/green]", selected_language)

    current_task = project_plan.tasks[project_plan.current_task - 1]
    console.log("> [green]Current task:[/green]", current_task.name)
    console.log("> [green]Task progress:[/green]", f"{project_plan.current_task}/{len(project_plan.tasks)}")
    console.log("> [green]Task description:[/green]", current_task.description)

    # start the interactive chat
    console.line()
    chat_app = Chat(model)
    # set the initial system prompt
    chat_app.add(role='system', content=pmpt_chat_init(selected_language, project_plan))
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
    debug_env = questionary.select(
        "Where do you want to launch the project?",
        choices=["cloud", "local", "not running"]
    ).ask()

    project_path = create_directory(name)
    update_project_plan(
        project_path,
        {
            'project_name': name,
            'current_task': 0,
            'description': description,
            'llm': configuration.read()['general']['platform'],
            'project': project_path,
            'lang': configuration.read()['general']['code_language'],
            'debug_env': debug_env
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


@cli.command()
@click.option('--port', '-p', default=8000, help="The port to run the server.")
@click.option('--address', '-a', default='0.0.0.0', help="The address to run the server.")
def server(port, address):
    """
    server: launch the MLE-Agent RESTful API server.
    :param port: the target port.
    :param address: the target address.
    :return: None
    """
    start_server(address, port)


@cli.command()
def status():
    """
    status: display the current status of the project.
    """
    configuration = Config()
    if configuration.read().get('project') is None:
        console.log("You have not set up a project yet.")
        console.log("Please create a new project first using 'mle new' command.")
        return

    project_path = configuration.read()['project']['path']
    project_plan = read_project_plan(str(os.path.join(project_path, CONFIG_PROJECT_FILE)))

    console.log("> [green]Current project:[/green]", project_plan.project_name)
    console.log("> [green]Project path:[/green]", project_path)
    console.log("> [green]Project entry file:[/green]", project_plan.entry_file)
    console.log("> [green]Project language:[/green]", project_plan.lang)
    console.line()
    # display the current task name
    current_task = project_plan.tasks[project_plan.current_task - 1]
    console.log("> [green]Current task:[/green]", current_task.name)
    console.log("> [green]Task progress:[/green]", f"{project_plan.current_task}/{len(project_plan.tasks)}")
    console.log("> [green]Task description:[/green]", current_task.description)

    if current_task.resources:
        console.line()
        console.log("> [green]Resources:[/green]")
        for resource in current_task.resources:
            console.log(f"- {resource.name}: {resource.uri}")

    if current_task.functions:
        console.line()
        console.log("> [green]Functions:[/green]")
        for function in current_task.functions:
            console.log(f"- {function.name}: {function.description}")

    if current_task.debug:
        console.line()
        console.log("> [green]Debugging:[/green]")
        console.log(f"- Maximum debug attempts: {current_task.debug}")
        console.log(f"- Debugging environment: {project_plan.debug_env}")
