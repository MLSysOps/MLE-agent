import sys

import click
import questionary

import agent
from agent.server import start_server
from agent.function import Chat, LeaderAgent
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


@click.group()
@click.version_option(version=agent.__version__)
def cli():
    """
    MLE-Agent: The CLI tool to build machine learning projects.
    """
    pass


@cli.group()
def project():
    """
    project: group of commands related to project management.
    """
    pass


@project.command()
@click.argument('name')
def delete(name):
    """
    delete: delete a machine learning project with the given NAME.
    """
    delete_project(name)


@project.command()
def switch():
    """
    switch: set the current project to work on.
    """
    projects = list_projects()
    project_names = [p.name for p in projects]
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


@project.command()
def ls():
    """
    ls: list all existing machine learning projects.
    """
    projects = list_projects()
    for p in projects:
        if p.description:
            print(f"- {p.name}: {p.description}")
        else:
            print(f"- {p.name}")


@project.command()
def show():
    """
    show: show the current project.
    """
    if configuration.read().get('project') is None:
        console.log("You have not set up a project yet.")
        console.log("Please create a new project first using 'mle new' command.")
        return

    project_name = configuration.read()['project']['name']
    target_project = read_project_state(project_name)
    print(target_project.dict())


@cli.command()
@click.option('--general', '-g', is_flag=True, help="Set up the general configuration for MLE Agent.")
def config(general):
    """
    Set up the global configuration for MLE-agent.
    """
    build_config(general)


@cli.command()
@click.option('--reset', '-r', is_flag=True, help="Reset the project state.")
def start(reset=False):
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

    if os.path.exists(p.path):
        if p.kaggle_config:
            console.log("Starting Kaggle project...")
            from agent.integration.kaggle_workflow import KaggleAgent
            kaggle_agent = KaggleAgent(p, load_model())
            kaggle_agent.invoke()
        else:
            chain = LeaderAgent(p, load_model())
            chain.invoke()
    else:
        console.log(f"Project path'{p.path}' does not exist. Aborted.")


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
    target_project = read_project_state(project_name)

    console.log("> [green]Current project:[/green]", target_project.path)
    console.log("> [green]Project language:[/green]", target_project.lang)

    current_task = target_project.plan.tasks[target_project.plan.current_task - 1]
    console.log("> [green]Current task:[/green]", current_task.name)
    console.log("> [green]Task progress:[/green]",
                f"{target_project.plan.current_task}/{len(target_project.plan.tasks)}")
    console.log("> [green]Task description:[/green]", current_task.description)

    # start the interactive chat
    console.line()
    chat_app = Chat(model)
    # set the initial system prompt
    chat_app.add(role='system', content=pmpt_chat_init(target_project))
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

    is_kaggle = questionary.confirm("Is this a Kaggle project?").ask()

    if is_kaggle:
        kaggle_username = questionary.text("What is your Kaggle username?").ask()
        kaggle_key = questionary.text("What is your Kaggle API key?").ask()
        if not kaggle_username or not kaggle_key:
            console.log("Kaggle credentials are required for a Kaggle project. Aborted.")
            return
        kaggle_config = {
            "username": kaggle_username,
            "key": kaggle_key
        }
    else:
        kaggle_config = None

    description = questionary.text("What is the description of this project? (Optional)").ask()
    create_project(
        Project(
            name=name,
            description=description,
            lang=configuration.read()['general']['code_language'],
            llm=configuration.read()['general']['platform'],
            exp_track=configuration.read()['general']['experiment_tracking_tool'],
            kaggle_config=kaggle_config
        ),
        set_current=True
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


@cli.command()
def status():
    """
    status: display the current status of the project.
    """
    if configuration.read().get('project') is None:
        console.log("You have not set up a project yet.")
        console.log("Please create a new project first using 'mle new' command.")
        return

    project_name = configuration.read()['project'].get('name')
    if not project_name:
        console.log(
            "Currently no working project. "
            "Please use `mle project switch` to set a project or use `mle new` to create a new project."
        )
        return

    target_project = read_project_state(project_name)

    console.print("> [green]Current project:[/green]", target_project.name)
    console.print("> [green]Project path:[/green]", target_project.path)
    console.print("> [green]Project entry file:[/green]", target_project.entry_file)
    console.print("> [green]Project language:[/green]", target_project.lang)
    console.line()

    if target_project.plan:
        # display the current task name
        current_task = target_project.plan.tasks[target_project.plan.current_task - 1]
        console.print("> [green]Current task:[/green]", current_task.name)
        console.print("> [green]Task progress:[/green]",
                      f"{target_project.plan.current_task}/{len(target_project.plan.tasks)}")
        console.print("> [green]Task description:[/green]", current_task.description)

        if current_task.resources:
            console.line()
            console.print("> [green]Resources:[/green]")
            for resource in current_task.resources:
                console.print(f"- {resource.name}: {resource.uri}")

        if current_task.functions:
            console.line()
            console.print("> [green]Functions:[/green]")
            for function in current_task.functions:
                console.print(f"- {function.name}: {function.description}")

        if current_task.debug:
            console.line()
            console.print("> [green]Debugging:[/green]")
            console.print(f"- Maximum debug attempts: {current_task.debug}")
            console.print(f"- Debugging environment: {target_project.debug_env}")
