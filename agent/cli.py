import sys

import click
import questionary

import agent
from agent.server import start_server
from agent.function import Chat, LeaderAgent
from agent.model import OpenAIModel, OllamaModel
from agent.utils import *
from agent.types import Project

console = Console()
configuration = Config()


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
    if configuration.read() is None:
        build_config()

    if configuration.read().get('project') is None:
        console.log("You have not set up a project yet.")
        console.log("Please create a new project first using 'mle new your_project_name' command,"
                    " or set the project using 'mle set_project <project path>'.")
        return

    project = read_project_state(configuration.read()['project']['name'])
    if project is None:
        console.log("Could not find the project in the database. Aborted.")
        return

    chain = LeaderAgent(project, load_model())
    chain.start()


@cli.command()
def chat():
    """
    chat: start an interactive chat with LLM to work on your ML project.
    """
    # check the system configuration
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

    project_name = configuration.read()['project']['name']
    project = read_project_state(project_name)

    console.log("> [green]Current project:[/green]", project.path)

    selected_language = project.lang
    console.log("> [green]Project language:[/green]", selected_language)

    current_task = project.plan.tasks[project.plan.current_task - 1]
    console.log("> [green]Current task:[/green]", current_task.name)
    console.log("> [green]Task progress:[/green]", f"{project.plan.current_task}/{len(project.plan.tasks)}")
    console.log("> [green]Task description:[/green]", current_task.description)

    # start the interactive chat
    console.line()
    chat_app = Chat(model)
    # set the initial system prompt
    chat_app.add(role='system', content=pmpt_chat_init(selected_language, project))
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

    description = questionary.text("What is the description of this project? (Optional)").ask()
    project_path = create_directory(name)
    update_project_state(Project(
        name=name,
        path=project_path,
        description=description,
        lang=configuration.read()['general']['code_language'],
        llm=configuration.read()['general']['platform'],
    ))

    # write the project configuration
    configuration.write_section(
        CONFIG_SEC_PROJECT, {
            'path': project_path,
            'name': name
        }
    )


@cli.command()
@click.option('--port', '-p', default=8000, help="The port to run the server.")
@click.option('--address', '-a', default='0.0.0.0', help="The address to run the server.")
def server(port, address):
    """
    server: launch the MLE-Agent RESTFul API server.
    :param port: the target port.
    :param address: the target address.
    :return: None
    """
    start_server(address, port)


# a CLI command to set project
@cli.command()
def set_project():
    """
    set_project: set the current project to work on.
    :return: None
    """
    projects = list_projects()
    project_names = [project.name for project in projects]
    target_name = questionary.select(
        "Select the project to work on:",
        choices=project_names
    ).ask()

    if target_name:
        target_project = read_project_state(target_name)
        configuration.write_section(
            CONFIG_SEC_PROJECT, {
                'path': target_project.path,
                'name': target_project.name
            }
        )
        console.log(f"Project set to: {target_name}")


@cli.command()
def status():
    """
    status: display the current status of the project.
    """
    if configuration.read().get('project') is None:
        console.log("You have not set up a project yet.")
        console.log("Please create a new project first using 'mle new' command.")
        return

    project_name = configuration.read()['project']['name']
    project = read_project_state(project_name)

    console.log("> [green]Current project:[/green]", project.name)
    console.log("> [green]Project path:[/green]", project.path)
    console.log("> [green]Project entry file:[/green]", project.entry_file)
    console.log("> [green]Project language:[/green]", project.lang)
    console.line()
    # display the current task name
    current_task = project.plan.tasks[project.plan.current_task - 1]
    console.log("> [green]Current task:[/green]", current_task.name)
    console.log("> [green]Task progress:[/green]", f"{project.plan.current_task}/{len(project.plan.tasks)}")
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
        console.log(f"- Debugging environment: {project.debug_env}")
