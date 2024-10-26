"""
Local Report Mode: the mode to generate the AI report based on users' local github repo
"""
from rich.console import Console
from mle.model import load_model
from mle.agents import ReportAgent, GitSummaryAgent


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
