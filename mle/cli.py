import os
import re
import yaml
import click
import pickle
import uvicorn
import questionary
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, TextColumn, BarColumn
import json

import mle
from mle.server import app
import mle.workflow as workflow
from mle.utils.system import (
    get_config,
    write_config,
    check_config,
    startup_web,
    print_in_box,
)
from mle.utils import CodeChunker
from mle.utils import LanceDBMemory, list_files, read_file
from mle.utils.component_memory import ComponentMemory

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
@click.pass_context
@click.argument('path', default='./')
@click.option('--email', default=None, help='The email of the user.')
@click.option('--start-date', default=None, help='The start date of the user activity (YYYY-MM-DD).')
@click.option('--end-date', default=None, help='The end date of the user activity (YYYY-MM-DD).')
def report_local(ctx, path, email, start_date, end_date):
    """
    report_local: generate report with LLM for local git repo.
    """
    if not check_config(console):
        return

    if email is None:
        email = questionary.text(
            "What is your Git email? (e.g., huangyz0918@gmail.com)"
        ).ask()

    return workflow.report_local(os.getcwd(), path, email, start_date=start_date, end_date=end_date)


@cli.command()
@click.option('--model', default=None, help='The model to use for the chat.')
@click.option('--auto', is_flag=True, help='Use auto mode to generate the coding plan.')
@click.option('--description', default=None, help='The description of the competition.')
@click.option('--datasets', default=None, help='The .csv dataset home to use for the competition.')
@click.option('--submission', default='./submission.csv', help='the path of the kaggle submission .csv file.')
@click.option('--sub_example', default=None, help='the path to the kaggle submission example .csv file.')
@click.option('--comp_id', default=None, help='the kaggle competition id.')
@click.option('--debug_max_attempt', default=5, help='the max attempt for debugging.')
def kaggle(
        model,
        auto,
        description=None,
        datasets=None,
        sub_example=None,
        submission='.',
        comp_id=None,
        debug_max_attempt=5
):
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
            competition_id=comp_id,
            debug_max_attempt=debug_max_attempt
        )

    return workflow.kaggle(os.getcwd(), model)


@cli.command()
@click.option('--model', default=None, help='The model to use for the chat.')
@click.option('--build_mem', is_flag=True, help='Build and enable the local memory for the chat.')
def chat(model, build_mem):
    """
    chat: start an interactive chat with LLM to work on your ML project.
    """
    if not check_config(console):
        return

    memory = LanceDBMemory(os.getcwd())
    if build_mem:
        working_dir = os.getcwd()
        table_name = 'mle_chat_' + working_dir.split('/')[-1]
        source_files = list_files(working_dir, ['*.py'])  # TODO: support more file types

        chunker = CodeChunker(os.path.join(working_dir, '.mle', 'cache'), 'py')
        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console,
        ) as progress:
            process_task = progress.add_task("Processing files...", total=len(source_files))

            for file_path in source_files:
                raw_code = read_file(file_path)
                progress.update(
                    process_task,
                    advance=1,
                    description=f"Adding {os.path.basename(file_path)} to memory..."
                )

                chunks = chunker.chunk(raw_code, token_limit=100)
                memory.add(
                    texts=list(chunks.values()),
                    table_name=table_name,
                    metadata=[{'file': file_path, 'chunk_key': k} for k, _ in chunks.items()]
                )

    return workflow.chat(os.getcwd(), model=model, memory=memory)


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
    new: create a new project.
    """
    if not name:
        console.log("Please provide a valid project name. Aborted.")
        return

    # First, ask for the type of platform/engine
    platform_type = questionary.select(
        "What type of LLM platform or engine do you want to use?",
        choices=['API Platform', 'Local Engine']
    ).ask()

    api_key = None
    base_url = None
    model_name = None
    platform = None

    if platform_type == 'API Platform':
        # API-based platforms
        platform = questionary.select(
            "Which API platform do you want to use?",
            choices=['OpenAI', 'Claude', 'Gemini', 'MistralAI', 'DeepSeek']
        ).ask()

        if platform == 'OpenAI':
            api_key = questionary.password("What is your OpenAI API key?").ask()
            if not api_key:
                console.log("API key is required. Aborted.")
                return
            model_name = questionary.text(
                "What model do you want to use? (default: gpt-4o-2024-08-06)"
            ).ask() or "gpt-4o-2024-08-06"

        elif platform == 'Claude':
            api_key = questionary.password("What is your Anthropic API key?").ask()
            if not api_key:
                console.log("API key is required. Aborted.")
                return
            model_name = questionary.text(
                "What model do you want to use? (default: claude-3-5-sonnet-20240620)"
            ).ask() or "claude-3-5-sonnet-20240620"

        elif platform == 'MistralAI':
            api_key = questionary.password("What is your MistralAI API key?").ask()
            if not api_key:
                console.log("API key is required. Aborted.")
                return
            model_name = questionary.text(
                "What model do you want to use? (default: mistral-large-latest)"
            ).ask() or "mistral-large-latest"

        elif platform == 'DeepSeek':
            api_key = questionary.password("What is your DeepSeek API key?").ask()
            if not api_key:
                console.log("API key is required. Aborted.")
                return
            model_name = questionary.text(
                "What model do you want to use? (default: deepseek-coder)"
            ).ask() or "deepseek-coder"

        elif platform == 'Gemini':
            api_key = questionary.password("What is your Gemini API key?").ask()
            if not api_key:
                console.log("API key is required. Aborted.")
                return
            model_name = questionary.text(
                "What model do you want to use? (default: gemini-2.5-flash)"
            ).ask() or "gemini-2.5-flash"

    elif platform_type == 'Local Engine':
        # Local engines
        platform = questionary.select(
            "Which local engine do you want to use?",
            choices=['Ollama', 'vLLM']
        ).ask()

        if platform == 'Ollama':
            model_name = questionary.text(
                "What model do you want to use? (default: llama3)"
            ).ask() or "llama3"
            
            host_url = questionary.text(
                "What is your Ollama host URL? (default: http://localhost:11434)"
            ).ask() or "http://localhost:11434"
            base_url = host_url

        elif platform == 'vLLM':
            base_url = questionary.text(
                "What is your vLLM server URL? (default: http://localhost:8000/v1)"
            ).ask() or "http://localhost:8000/v1"

            model_name = questionary.text(
                "What is the model name loaded in your vLLM server? (default: Qwen/Qwen2.5-1.5B-Instruct)"
            ).ask() or "Qwen/Qwen2.5-1.5B-Instruct"

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
            'base_url': base_url,
            'model': model_name,
        }, outfile, default_flow_style=False)


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


@cli.command()
@click.option('--add', default=None, help='Add files or directories into the local memory.')
@click.option('--rm', default=None, help='Remove files or directories into the local memory.')
@click.option('--update', default=None, help='Update files or directories into the local memory.')
def memory(add, rm, update):
    memory = LanceDBMemory(os.getcwd())
    path = add or rm or update
    if path is None:
        return

    source_files = []
    if os.path.isdir(path):
        source_files = list_files(path, ['*.py'])
    else:
        source_files = [path]

    working_dir = os.getcwd()
    table_name = 'mle_chat_' + working_dir.split('/')[-1]
    chunker = CodeChunker(os.path.join(working_dir, '.mle', 'cache'), 'py')
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        process_task = progress.add_task("Processing files...", total=len(source_files))

        for file_path in source_files:
            raw_code = read_file(file_path)
            progress.update(
                process_task,
                advance=1,
                description=f"Process {os.path.basename(file_path)} for memory..."
            )

            if add:
                # add file into memory
                chunks = chunker.chunk(raw_code, token_limit=100)
                memory.add(
                    texts=list(chunks.values()),
                    table_name=table_name,
                    metadata=[{'file': file_path, 'chunk_key': k} for k, _ in chunks.items()]
                )
            elif rm:
                # remove file from memory
                memory.delete_by_metadata(
                    key="file",
                    value=file_path,
                    table_name=table_name,
                )
            elif update:
                # update file into memory
                chunks = chunker.chunk(raw_code, token_limit=100)
                memory.delete_by_metadata(
                    key="file",
                    value=file_path,
                    table_name=table_name,
                )
                memory.add(
                    texts=list(chunks.values()),
                    table_name=table_name,
                    metadata=[{'file': file_path, 'chunk_key': k} for k, _ in chunks.items()]
                )


@cli.command()
@click.option('--component', type=click.Choice([
    'advisor', 'planner', 'coder', 'debugger', 'reporter', 'chat',
    'github_summarizer', 'git_summarizer'
]), help='Component to view traces for')
@click.option('--limit', default=5, help='Maximum number of traces to show')
@click.option('--full-output', is_flag=True, help='Show complete output (not truncated)')
def traces(component, limit, full_output):
    """View execution traces for components."""
    if not component:
        console.print("[yellow]Please specify a component to view traces for.[/yellow]")
        return

    memory = ComponentMemory(os.getcwd())
    traces = memory.get_recent_traces(component, limit)

    if not traces:
        console.print(f"[yellow]No traces found for component: {component}[/yellow]")
        return

    console.print(f"[green]Recent {component} traces:[/green]")

    for i, trace in enumerate(traces):
        console.print(f"\n[bold cyan]Trace #{i+1}[/bold cyan] ({trace['timestamp']})")
        console.print(f"Status: {trace['status']}")

        if trace['execution_time']:
            console.print(f"Execution Time: {trace['execution_time']:.2f} seconds")

        # Show context information
        if trace['context']:
            context = trace['context']
            if isinstance(context, dict) and context:
                console.print("\n[bold]Context:[/bold]")
                for key, value in context.items():
                    console.print(f"  {key}: {value}")

        # Show full input
        console.print("\n[bold]Input:[/bold]")
        if isinstance(trace['input_data'], str):
            if full_output:
                console.print(trace['input_data'])
            else:
                console.print(trace['input_data'][:500] + ("..." if len(trace['input_data']) > 500 else ""))
        else:
            # Handle dictionary or other structured data
            input_str = json.dumps(trace['input_data'], indent=2) if isinstance(trace['input_data'], (dict, list)) else str(trace['input_data'])
            if full_output:
                console.print(input_str)
            else:
                console.print(input_str[:500] + ("..." if len(input_str) > 500 else ""))

        # Show full output
        console.print("\n[bold]Output:[/bold]")
        if isinstance(trace['output_data'], str):
            if full_output:
                console.print(trace['output_data'])
            else:
                console.print(trace['output_data'][:500] + ("..." if len(trace['output_data']) > 500 else ""))
        else:
            # Handle dictionary or other structured data
            output_str = json.dumps(trace['output_data'], indent=2) if isinstance(trace['output_data'], (dict, list)) else str(trace['output_data'])
            if full_output:
                console.print(output_str)
            else:
                console.print(output_str[:500] + ("..." if len(output_str) > 500 else ""))

        console.print("-" * 50)

    # Show command for seeing full output
    if not full_output and traces:
        console.print("[yellow]Tip: Use --full-output flag to see complete trace data[/yellow]")

    memory.close()


# Experimental commands
try:
    from exp.cli import bench

    cli.add_command(bench, name='bench')
except ImportError:
    exp = None
