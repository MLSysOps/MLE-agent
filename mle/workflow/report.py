"""
Report Mode: the mode to generate the AI report based on the user's requirements.
"""
import os
import pickle
from rich.console import Console
from mle.model import load_model
from mle.utils.system import get_config, write_config, check_config
from mle.integration import GoogleCalendarIntegration, github_login
from mle.agents import GitHubSummaryAgent, ReportAgent, GitSummaryAgent


def ask_data(data_str: str):
    """
    Ask the user to provide the data information.
    :param data_str: the input data string. Now, it should be the name of the public dataset or
     the path to the local CSV file.
    :return: the formated data information.
    """
    if os.path.isfile(data_str) and data_str.lower().endswith('.csv'):
        return f"[green]CSV Dataset Location:[/green] {data_str}"
    else:
        return f"[green]Dataset:[/green] {data_str}"


def report(
        work_dir: str,
        github_repo: str,
        github_username: str,
        github_token: str = None,
        okr_str: str = None,
        model=None
):
    """
    The workflow of the baseline mode.
    :param work_dir: the working directory.
    :param github_repo: the GitHub repository.
    :param github_username: the GitHub username.
    :param github_token: the GitHub token.
    :param okr_str: the OKR string.
    :param model: the model to use.
    :return:
    """
    console = Console()
    model = load_model(work_dir, model)

    events = None
    if check_config(console):
        config = get_config()
        if github_token is None:
            if "github" in config.get("integration", {}).keys():
                github_token = config["integration"]["github"].get("token")
            else:
                github_token = github_login()
                config["integration"]["github"] = {"token": github_token}
                write_config(config)

        if "google_calendar" in config.get("integration", {}).keys():
            google_token = pickle.loads(config["integration"]["google_calendar"].get("token"))
            google_calendar = GoogleCalendarIntegration(google_token)
            events = google_calendar.get_events()

    summarizer = GitHubSummaryAgent(
        model,
        github_repo=github_repo,
        username=github_username,
        github_token=github_token,
    )
    reporter = ReportAgent(model, console)

    github_summary = summarizer.summarize()
    return reporter.gen_report(github_summary, events, okr=okr_str)


def report_local(
        work_dir: str,
        git_path: str,
        email: str,
        okr_str: str = None,
        start_date: str = None,
        end_date: str = None,
        model=None
):
    """
    The workflow of the baseline mode.
    :param work_dir: the working directory.
    :param git_path: the path to the local Git repository.
    :param email: the email address.
    :param okr_str: the OKR string.
    :param start_date: the start date.
    :param end_date: the end date.
    :param model: the model to use.
    :return:
    """

    console = Console()
    model = load_model(work_dir, model)

    events = None

    summarizer = GitSummaryAgent(
        model,
        git_path=git_path,
        git_email=email,
    )
    reporter = ReportAgent(model, console)

    git_summary = summarizer.summarize(start_date=start_date, end_date=end_date)
    return reporter.gen_report(git_summary, events, okr=okr_str)
