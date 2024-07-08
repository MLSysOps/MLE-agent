"""
Baseline Mode: the mode to quickly generate the AI baseline based on the user's requirements.
"""
from rich.console import Console
from mle.model import load_model
from mle.agents import CodeAgent, DebugAgent, AdviseAgent, PlanAgent


def baseline(work_dir: str):
    """
    The workflow of the baseline mode.
    :return:
    """
    console = Console()
    ml_requirement = "I want to build an image classification model."

    console.print(f"[blue]User:[/blue] {ml_requirement}")
    model = load_model(work_dir, 'gpt-4o')

    advisor = AdviseAgent(model)
    suggestion = advisor.suggest(ml_requirement)
    enhanced_requirement = f"""
    The user's requirement: {ml_requirement}
    The ML task: {suggestion.get('task')},
    The model: {suggestion.get('model')},
    The dataset: {suggestion.get('dataset')},
    The reference: {suggestion.get('reference')},
    The evaluation metric: {suggestion.get('evaluation_metric')}
    """
    console.print(f"[green]Advisor:[/green] {enhanced_requirement}")

    planner = PlanAgent(model)
    coding_plan = planner.plan(enhanced_requirement)
    console.print(f"[orange]Planner:[/orange] {coding_plan}")

    coder = CodeAgent(model, work_dir)
    debugger = DebugAgent(model)

    for current_task in coding_plan.get('tasks'):
        task_requirement = f"""
        You are required to complete task: {current_task.get('task')}.\n
        You should: {current_task.get('description')}
        """

        code_report = coder.code(task_requirement)
        code_prompt = f"""
        I have finish the task: {current_task.get('task')}. {code_report.get('message')}\n
        The dependencies required to run the code: {code_report.get('dependency')}\n
        The command to run the code: {code_report.get('command')}\n
        Whether the code is required to test and debug: {code_report.get('debug')}
        """
        console.print(f"[cyan]Developer:[/cyan] {code_prompt}")

        while True:
            if code_report.get('debug') == 'true':
                debug_report = debugger.analyze(code_prompt)
                if debug_report.get('status') == 'success':
                    break
                else:
                    improve_prompt = f"""
                    You are required improve the existing project.
                    The required changes: {debug_report.get("changes")}
                    The suggestion: {debug_report.get("suggestion")}
                    
                    """
                    console.print(f"[yellow]Debugger:[/yellow] {improve_prompt}")
                    code_report = coder.code(improve_prompt)
            else:
                break
