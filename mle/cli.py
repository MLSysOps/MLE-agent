import os
import re
import yaml
import click
import pickle
import uvicorn
import questionary
from pathlib import Path
from rich.console import Console

import mle
from mle.server import app
import mle.workflow as workflow
from mle.utils import Memory
from mle.utils.system import (
    get_config,
    write_config,
    check_config,
    startup_web,
    print_in_box,
)

console = Console()


@click.group()
@click.version_option(version=mle.__version__)
def cli():
    """
    MLE-Agent: The CLI tool to build machine learning projects.
    """
    pass


@cli.command()
@click.pass_context
@click.argument('mode', default='baseline')
@click.option('--model', default=None, help='The model to use for the chat.')
def start(ctx, mode, model):
    """
    start: start the chat with LLM.
    """
    if not check_config(console):
        return

    if mode == 'baseline':
        # Baseline mode
        return workflow.baseline(os.getcwd(), model)
    elif mode == 'report':
        # Report mode
        return ctx.invoke(report, model=model, visualize=False)
    elif mode == 'kaggle':
        # Kaggle mode
        return ctx.invoke(kaggle, model=model)
    elif mode == 'chat':
        # Chat mode
        return ctx.invoke(chat, model=model)
    else:
        raise ValueError("Invalid mode. Supported modes: 'baseline', 'report', 'kaggle'.")


@cli.command()
@click.pass_context
@click.argument('repo', required=False)
@click.option('--model', default=None, help='The model to use for the chat.')
@click.option('--user', default=None, help='The GitHub username.')
@click.option('--visualize', default=True, help='Visualize the report in browser.')
def report(ctx, repo, model, user, visualize):
    """
    report: generate report with LLM.
    """
    if visualize:
        print_in_box(
            "✨ Your MLE Agent is starting! \n"
            "Access to generate your report: "
            "[blue underline]http://localhost:3000/[/blue underline]",
            console=console, title="MLE Report", color="green"
        )
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor() as executor:
            future1 = executor.submit(ctx.invoke, serve)
            future2 = executor.submit(ctx.invoke, web)
            future1.result()
            future2.result()
    else:
        if repo is None:
            # TODO: support local project report
            repo = questionary.text(
                "What is your GitHub repository? (e.g., MLSysOps/MLE-agent)"
            ).ask()

        if user is None:
            user = questionary.text(
                "What is your GitHub username? (e.g., huangyz0918)"
            ).ask()

        if not re.match(r'.*/.*', repo):
            console.log("Invalid github repository, "
                        "Usage: 'mle report <organization/name>'")
            return False

        if not check_config(console):
            # build a new project for GitHub report generating
            project_name = f"mle-report-{repo.replace('/', '_').lower()}"
            ctx.invoke(new, name=project_name)
            work_dir = os.path.join(os.getcwd(), project_name)
            os.chdir(work_dir)
            return workflow.report(work_dir, repo, user, model)
        return workflow.report(os.getcwd(), repo, user, model)


@cli.command()
@click.option('--model', default=None, help='The model to use for the chat.')
@click.option('--auto', is_flag=True, help='Use auto mode to generate the coding plan.')
@click.option('--description', default=None, help='The description of the competition.')
@click.option('--datasets', default=None, help='The .csv dataset home to use for the competition.')
@click.option('--submission', default='./submission.csv', help='the path of the kaggle submission .csv file.')
@click.option('--sub_example', default=None, help='the path to the kaggle submission example .csv file.')
@click.option('--comp_id', default=None, help='the kaggle competition id.')
def kaggle(model, auto, description=None, datasets=None, sub_example=None, submission='.', comp_id=None):
    """
    kaggle: kaggle competition workflow.

    Example command for auto mode:
    mle kaggle --auto --datasets "/Users/huangyz0918/desktop/spaceship-titanic/prepared/public/train.csv,/Users/huangyz0918/desktop/spaceship-titanic/prepared/public/test.csv"
     --description "/Users/huangyz0918/desktop/spaceship-titanic/prepared/public/description.md" --submission "./submission.csv"
     --sub_example "/Users/huangyz0918/desktop/spaceship-titanic/prepared/public/sample_submission.csv" --comp_id "spaceship-titanic"
    """
    if not check_config(console):
        return

    if auto:
        if datasets is None:
            datasets = questionary.text(
                "Please provide the dataset home path"
            ).ask()
        datasets = datasets.split(',')

        if description is None:
            description = questionary.text(
                "Please provide the competition description."
            ).ask()

        return workflow.auto_kaggle(
            os.getcwd(),
            datasets,
            description,
            submission=submission,
            model=model,
            sub_examples=sub_example,
            competition_id=comp_id
        )

    return workflow.kaggle(os.getcwd(), model)


@cli.command()
@click.option('--model', default=None, help='The model to use for the chat.')
def chat(model):
    """
    chat: start an interactive chat with LLM to work on your ML project.
    """
    if not check_config(console):
        return

    return workflow.chat(os.getcwd(), model)


@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind the server to')
@click.option('--port', default=8000, help='Port to bind the server to')
def serve(host, port):
    """Start the FastAPI server"""
    click.echo(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="critical")


@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind the server to')
@click.option('--port', default=3000, help='Port to bind the server to')
def web(host, port):
    """Start the Web server"""
    click.echo(f"Starting web on {host}:{port}")
    startup_web(host, port)


@cli.command()
@click.argument('name')
def new(name):
    """
    new: create a new machine learning project with the given NAME.
    """
    if not name:
        console.log("Please provide a valid project name. Aborted.")
        return

    platform = questionary.select(
        "Which language model platform do you want to use?",
        choices=['OpenAI', 'Ollama', 'Claude', 'MistralAI', 'DeepSeek']
    ).ask()

    api_key = None
    if platform == 'OpenAI':
        api_key = questionary.password("What is your OpenAI API key?").ask()
        if not api_key:
            console.log("API key is required. Aborted.")
            return

    elif platform == 'Claude':
        api_key = questionary.password("What is your Anthropic API key?").ask()
        if not api_key:
            console.log("API key is required. Aborted.")
            return

    elif platform == 'MistralAI':
        api_key = questionary.password("What is your MistralAI API key?").ask()
        if not api_key:
            console.log("API key is required. Aborted.")
            return

    elif platform == 'DeepSeek':
        api_key = questionary.password("What is your DeepSeek API key?").ask()
        if not api_key:
            console.log("API key is required. Aborted.")
            return

    search_api_key = questionary.password("What is your Tavily API key? (if no, the web search will be disabled)").ask()
    if search_api_key:
        os.environ["SEARCH_API_KEY"] = search_api_key

    # make a directory for the project
    project_dir = os.path.join(os.getcwd(), name)
    config_dir = os.path.join(project_dir, '.mle')
    Path(config_dir).mkdir(parents=True, exist_ok=True)
    with open(os.path.join(config_dir, 'project.yml'), 'w') as outfile:
        yaml.dump({
            'platform': platform,
            'api_key': api_key,
            'search_key': search_api_key,
            'integration': {},
        }, outfile, default_flow_style=False)

    # init the memory
    Memory(project_dir)


@cli.command()
@click.option('--reset', is_flag=True, help='Reset the integration')
def integrate(reset):
    """
    integrate: integrate the third-party extensions.
    """
    if not check_config(console):
        return

    config = get_config()
    if "integration" not in config.keys():
        config["integration"] = {}

    platform = questionary.select(
        "Which platform do you want to integrate?",
        choices=['GitHub', 'Google Calendar', 'Kaggle']
    ).ask()

    if platform == "GitHub":
        from mle.integration.github import github_login
        if not reset and config.get("integration").get("github"):
            print("GitHub is already integrated.")
        else:
            token = github_login()
            config["integration"]["github"] = {
                "token": token
            }
            write_config(config)

    elif platform == "Google Calendar":
        from mle.integration.google_calendar import google_calendar_login
        if not reset and get_config().get("integration").get("google_calendar"):
            print("Google Calendar is already integrated.")
        else:
            token = google_calendar_login()
            config["integration"]["google_calendar"] = {
                "token": pickle.dumps(token, fix_imports=False),
            }
            write_config(config)
