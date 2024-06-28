import click

import agent
from agent.function import Chat, LeaderAgent
from agent.server import start_server
from agent.utils import *
from agent.utils import configuration, build_config, console
from .kaggle_cli import kaggle


@click.group()
@click.version_option(version=agent.__version__)
def cli():
    """
    MLE-Agent: The CLI tool to build machine learning projects.
    """
    pass


cli.add_command(kaggle)


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
        console.log("Configuration file does not exist. Creating a new one...")
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

    description = questionary.text("What is the description of this project? (Optional)").ask()
    create_project(
        Project(
            name=name,
            description=description,
            lang=configuration.read()['general']['code_language'],
            llm=configuration.read()['general']['platform'],
            exp_track=configuration.read()['general']['experiment_tracking_tool'],
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
