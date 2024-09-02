"""
Report Mode: the mode to generate the AI report based on the user's requirements.
"""
import os
import json
import pickle
import datetime
from rich.console import Console
from mle.model import load_model
from mle.agents import SummaryAgent
from mle.utils import print_in_box, ask_text, get_config


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


def get_current_week_github_activities():
    """
    Get user's Github activities on this week.
    """
    config = get_config()
    if not (config.get("integration") and config["integration"].get("github")):
        return None

    token = config["integration"]["github"]["token"]
    repos = config["integration"]["github"]["repositories"]
    current_date = datetime.date.today()

    from mle.integration.github import GitHubIntegration
    activities = {}
    for repo in repos:
        github = GitHubIntegration(repo, token)
        start_date = current_date - datetime.timedelta(days=current_date.weekday())
        activities[repo] = github.get_user_activity(
            username=github.get_user_info()["login"],
            start_date=start_date.strftime('%Y-%m-%d'),
        )
    return activities


def get_current_week_google_calendar_activities():
    """
    Get user's google calendar events on this week.
    """
    config = get_config()
    if not (config.get("integration") and config["integration"].get("google_calendar")):
        return None

    # refresh google calendar activities
    token = pickle.loads(config["integration"]["google_calendar"]["token"])
    current_date = datetime.date.today()

    from mle.integration.google_calendar import GoogleCalendarIntegration
    google_calendar = GoogleCalendarIntegration(token)
    start_date = current_date - datetime.timedelta(days=current_date.weekday())
    end_date = start_date + datetime.timedelta(days=6)
    return google_calendar.get_events(
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
    )


def report(work_dir: str, model='gpt-4o'):
    """
    The workflow of the baseline mode.
    :return:
    """

    console = Console()
    model = load_model(work_dir, model)

    # fetch activities
    # github_activities = get_current_week_github_activities()
    # google_calendar_activities = get_current_week_google_calendar_activities()

    github_repo = ask_text("Please provide your github repository (organization/name)")
    if not github_repo:
        print_in_box("The user's github_repo is empty. Aborted", console, title="Error", color="red")
        return

    summarizer = SummaryAgent(model, github_repo=github_repo)
    github_summary = summarizer.summarize()
    print_in_box(json.dumps(github_summary), console, title="Github Summarizer", color="green")
